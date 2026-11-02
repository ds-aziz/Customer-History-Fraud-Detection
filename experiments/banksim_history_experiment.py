#!/usr/bin/env python3
"""
BankSim limited-history fraud-detection experiment.

Research question:
Does customer-specific past transaction behavior improve fraud detection,
especially when only a small amount of customer history is available?

Leakage rule:
For a transaction on day t, history features use only transactions from days < t.
Transactions from the same day are never used as history because BankSim provides
day-level timestamps (step) and no reliable within-day ordering.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42

BASE_FEATURES = ["age", "gender", "merchant", "category", "amount"]
CAT_FEATURES = ["age", "gender", "merchant", "category"]

HISTORY_FEATURES = [
    "previous_transaction_count",
    "previous_amount_mean",
    "previous_amount_std",
    "previous_amount_max",
    "previous_day_amount_mean",
    "amount_vs_previous_mean",
    "has_previous_history",
]

HISTORY_ORDER = ["0", "1", "2-3", "4-5", "6-10", "11-20", "21+"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to BankSim CSV")
    parser.add_argument("--output-dir", default="results/banksim_history")
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    return parser.parse_args()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().strip("'").strip('"') for c in df.columns]

    for col in ["customer", "age", "gender", "merchant", "category"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.strip("'")
                .str.strip('"')
            )

    return df


def validate_schema(df: pd.DataFrame) -> None:
    required = {
        "step",
        "customer",
        "age",
        "gender",
        "merchant",
        "category",
        "amount",
        "fraud",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required BankSim columns: {missing}")


def add_past_only_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build customer-history features from strictly earlier days only.

    Same-day transactions are first aggregated. Cumulative statistics are then
    shifted/excluded so that no transaction on the current day can leak into
    another transaction from that same day.
    """
    df = df.copy()
    df["_row_id"] = np.arange(len(df))

    daily = (
        df.groupby(["customer", "step"], as_index=False)
        .agg(
            day_txn_count=("amount", "size"),
            day_amount_sum=("amount", "sum"),
            day_amount_sumsq=("amount", lambda s: float(np.square(s).sum())),
            day_amount_max=("amount", "max"),
            day_amount_mean=("amount", "mean"),
        )
        .sort_values(["customer", "step"])
    )

    grouped = daily.groupby("customer", sort=False)

    daily["previous_transaction_count"] = (
        grouped["day_txn_count"].cumsum() - daily["day_txn_count"]
    )
    daily["previous_amount_sum"] = (
        grouped["day_amount_sum"].cumsum() - daily["day_amount_sum"]
    )
    daily["previous_amount_sumsq"] = (
        grouped["day_amount_sumsq"].cumsum() - daily["day_amount_sumsq"]
    )

    daily["previous_amount_max"] = grouped["day_amount_max"].transform(
        lambda s: s.cummax().shift(1)
    )

    # Exact last transaction is unknowable within a day, so use the mean amount
    # from the previous observed day instead of inventing a within-day ordering.
    daily["previous_day_amount_mean"] = grouped["day_amount_mean"].shift(1)

    n = daily["previous_transaction_count"].astype(float)
    s = daily["previous_amount_sum"].astype(float)
    ss = daily["previous_amount_sumsq"].astype(float)

    daily["previous_amount_mean"] = np.where(n > 0, s / n, np.nan)

    variance_numerator = ss - np.where(n > 0, (s * s) / n, 0.0)
    daily["previous_amount_std"] = np.where(
        n > 1,
        np.sqrt(np.maximum(variance_numerator / (n - 1), 0.0)),
        np.nan,
    )

    history_columns = [
        "customer",
        "step",
        "previous_transaction_count",
        "previous_amount_mean",
        "previous_amount_std",
        "previous_amount_max",
        "previous_day_amount_mean",
    ]

    df = df.merge(
        daily[history_columns],
        on=["customer", "step"],
        how="left",
    )

    df["amount_vs_previous_mean"] = np.where(
        df["previous_amount_mean"].notna()
        & (df["previous_amount_mean"] > 0),
        df["amount"] / df["previous_amount_mean"],
        np.nan,
    )

    df["has_previous_history"] = (
        df["previous_transaction_count"] > 0
    ).astype(int)

    df["history_group"] = pd.cut(
        df["previous_transaction_count"],
        bins=[-0.5, 0.5, 1.5, 3.5, 5.5, 10.5, 20.5, np.inf],
        labels=HISTORY_ORDER,
        right=True,
    )

    return df.sort_values("_row_id").drop(columns=["_row_id"])


def split_customers(df: pd.DataFrame, seed: int):
    customers = df["customer"].drop_duplicates().to_numpy()

    train_customers, temp_customers = train_test_split(
        customers,
        test_size=0.30,
        random_state=seed,
    )

    val_customers, test_customers = train_test_split(
        temp_customers,
        test_size=0.50,
        random_state=seed,
    )

    train = df[df["customer"].isin(train_customers)].copy()
    val = df[df["customer"].isin(val_customers)].copy()
    test = df[df["customer"].isin(test_customers)].copy()

    assert set(train["customer"]).isdisjoint(val["customer"])
    assert set(train["customer"]).isdisjoint(test["customer"])
    assert set(val["customer"]).isdisjoint(test["customer"])

    return train, val, test


def prepare_features(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    x = df[features].copy()

    for col in CAT_FEATURES:
        if col in x.columns:
            x[col] = x[col].fillna("__MISSING__").astype(str)

    return x


def fit_model(train, val, features, iterations, seed):
    model = CatBoostClassifier(
        iterations=iterations,
        learning_rate=0.05,
        depth=7,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=seed,
        verbose=False,
        allow_writing_files=False,
    )

    model.fit(
        prepare_features(train, features),
        train["fraud"].astype(int),
        cat_features=[c for c in CAT_FEATURES if c in features],
        eval_set=(
            prepare_features(val, features),
            val["fraud"].astype(int),
        ),
        use_best_model=True,
        verbose=False,
    )

    return model


def safe_roc_auc(y_true, probabilities):
    if len(np.unique(y_true)) < 2:
        return np.nan
    return float(roc_auc_score(y_true, probabilities))


def safe_average_precision(y_true, probabilities):
    if np.sum(y_true) == 0:
        return np.nan
    return float(average_precision_score(y_true, probabilities))


def choose_f1_threshold(y_true, probabilities):
    thresholds = np.linspace(0.01, 0.99, 99)
    scores = [
        f1_score(y_true, probabilities >= threshold, zero_division=0)
        for threshold in thresholds
    ]
    return float(thresholds[int(np.argmax(scores))])


def calculate_metrics(y_true, probabilities, threshold):
    predictions = probabilities >= threshold

    return {
        "n": int(len(y_true)),
        "fraud_n": int(np.sum(y_true)),
        "fraud_rate": float(np.mean(y_true)),
        "pr_auc": safe_average_precision(y_true, probabilities),
        "roc_auc": safe_roc_auc(y_true, probabilities),
        "precision": float(
            precision_score(y_true, predictions, zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, predictions, zero_division=0)
        ),
        "f1": float(
            f1_score(y_true, predictions, zero_division=0)
        ),
        "threshold": float(threshold),
    }


def customer_bootstrap_pr_auc(
    test,
    simple_probabilities,
    history_probabilities,
    n_bootstrap,
    seed,
):
    rng = np.random.default_rng(seed)

    customers = test["customer"].drop_duplicates().to_numpy()

    work = test[["customer", "fraud"]].copy()
    work["simple_probability"] = simple_probabilities
    work["history_probability"] = history_probabilities

    customer_frames = {
        customer: group
        for customer, group in work.groupby("customer", sort=False)
    }

    differences = []

    for _ in range(n_bootstrap):
        sampled_customers = rng.choice(
            customers,
            size=len(customers),
            replace=True,
        )

        bootstrap_sample = pd.concat(
            [customer_frames[c] for c in sampled_customers],
            ignore_index=True,
        )

        y_true = bootstrap_sample["fraud"].to_numpy()

        if y_true.sum() == 0:
            continue

        simple_score = average_precision_score(
            y_true,
            bootstrap_sample["simple_probability"],
        )
        history_score = average_precision_score(
            y_true,
            bootstrap_sample["history_probability"],
        )

        differences.append(history_score - simple_score)

    if not differences:
        return {
            "mean_difference": np.nan,
            "ci95_low": np.nan,
            "ci95_high": np.nan,
            "bootstrap_replicates": 0,
        }

    differences = np.asarray(differences)

    return {
        "mean_difference": float(differences.mean()),
        "ci95_low": float(np.quantile(differences, 0.025)),
        "ci95_high": float(np.quantile(differences, 0.975)),
        "bootstrap_replicates": int(len(differences)),
    }


def main():
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.csv)
    df = normalize_columns(df)
    validate_schema(df)

    df["step"] = pd.to_numeric(df["step"], errors="raise")
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    df["fraud"] = pd.to_numeric(df["fraud"], errors="raise").astype(int)

    df = add_past_only_history(df)

    train, val, test = split_customers(df, args.seed)

    simple_features = BASE_FEATURES
    history_features = BASE_FEATURES + HISTORY_FEATURES

    simple_model = fit_model(
        train,
        val,
        simple_features,
        args.iterations,
        args.seed,
    )

    history_model = fit_model(
        train,
        val,
        history_features,
        args.iterations,
        args.seed,
    )

    simple_val_prob = simple_model.predict_proba(
        prepare_features(val, simple_features)
    )[:, 1]

    history_val_prob = history_model.predict_proba(
        prepare_features(val, history_features)
    )[:, 1]

    simple_threshold = choose_f1_threshold(
        val["fraud"].to_numpy(),
        simple_val_prob,
    )
    history_threshold = choose_f1_threshold(
        val["fraud"].to_numpy(),
        history_val_prob,
    )

    simple_test_prob = simple_model.predict_proba(
        prepare_features(test, simple_features)
    )[:, 1]

    history_test_prob = history_model.predict_proba(
        prepare_features(test, history_features)
    )[:, 1]

    overall = {
        "simple": calculate_metrics(
            test["fraud"].to_numpy(),
            simple_test_prob,
            simple_threshold,
        ),
        "history": calculate_metrics(
            test["fraud"].to_numpy(),
            history_test_prob,
            history_threshold,
        ),
    }

    overall["pr_auc_difference_history_minus_simple"] = (
        overall["history"]["pr_auc"]
        - overall["simple"]["pr_auc"]
    )

    overall["customer_bootstrap_pr_auc_difference"] = (
        customer_bootstrap_pr_auc(
            test,
            simple_test_prob,
            history_test_prob,
            args.bootstrap,
            args.seed,
        )
    )

    test = test.copy()
    test["simple_probability"] = simple_test_prob
    test["history_probability"] = history_test_prob

    group_rows = []

    for history_group in HISTORY_ORDER:
        group = test[
            test["history_group"].astype(str) == history_group
        ]

        if group.empty:
            continue

        simple_metrics = calculate_metrics(
            group["fraud"].to_numpy(),
            group["simple_probability"].to_numpy(),
            simple_threshold,
        )

        history_metrics = calculate_metrics(
            group["fraud"].to_numpy(),
            group["history_probability"].to_numpy(),
            history_threshold,
        )

        if (
            np.isnan(simple_metrics["pr_auc"])
            or np.isnan(history_metrics["pr_auc"])
        ):
            pr_auc_difference = np.nan
        else:
            pr_auc_difference = (
                history_metrics["pr_auc"]
                - simple_metrics["pr_auc"]
            )

        group_rows.append(
            {
                "history_group": history_group,
                "n": int(len(group)),
                "fraud_n": int(group["fraud"].sum()),
                "simple_pr_auc": simple_metrics["pr_auc"],
                "history_pr_auc": history_metrics["pr_auc"],
                "pr_auc_difference": pr_auc_difference,
                "simple_roc_auc": simple_metrics["roc_auc"],
                "history_roc_auc": history_metrics["roc_auc"],
                "simple_precision": simple_metrics["precision"],
                "history_precision": history_metrics["precision"],
                "simple_recall": simple_metrics["recall"],
                "history_recall": history_metrics["recall"],
                "simple_f1": simple_metrics["f1"],
                "history_f1": history_metrics["f1"],
            }
        )

    group_results = pd.DataFrame(group_rows)
    group_results.to_csv(
        output_dir / "history_group_results.csv",
        index=False,
    )

    prediction_columns = [
        "customer",
        "step",
        "amount",
        "fraud",
        "previous_transaction_count",
        "history_group",
        "simple_probability",
        "history_probability",
    ]

    test[prediction_columns].to_csv(
        output_dir / "test_predictions.csv",
        index=False,
    )

    summary = {
        "rows": int(len(df)),
        "customers": int(df["customer"].nunique()),
        "fraud_rows": int(df["fraud"].sum()),
        "split_customers": {
            "train": int(train["customer"].nunique()),
            "validation": int(val["customer"].nunique()),
            "test": int(test["customer"].nunique()),
        },
        "simple_features": simple_features,
        "history_features": history_features,
        "same_day_rule": (
            "History uses only transactions from strictly earlier step/day values."
        ),
        "overall": overall,
    }

    with open(
        output_dir / "summary.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(summary, file, indent=2)

    simple_model.save_model(
        str(output_dir / "simple_model.cbm")
    )
    history_model.save_model(
        str(output_dir / "history_model.cbm")
    )

    print(json.dumps(summary, indent=2))
    print("\nHistory-group results:")
    print(group_results.to_string(index=False))


if __name__ == "__main__":
    main()
