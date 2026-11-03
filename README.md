# Customer-History-Fraud-Detection

A controlled fraud-detection study of **how stable the benefit of customer-specific transaction history is across history lengths, unseen customers, and different datasets**.

## Research question

Prior research already shows that customer transaction history can improve fraud detection, and several studies have also examined low-frequency / cold-start users and the effect of available history.

This project therefore asks a narrower question:

> **Is there a stable or universal point at which customer-specific transaction history becomes reliably useful for fraud detection, or does that point depend on the dataset and transaction environment?**

The experiment compares two models using the same algorithm:

- **Simple model:** current transaction information only
- **History model:** the same current transaction information plus strictly past customer behavior

The project does **not** claim that using transaction history for fraud detection is itself novel. Its focus is the **stability and reproducibility of the history benefit** under a controlled evaluation protocol.

## Experimental design

- Datasets: BankSim and Sparkov
- Split: customers/cards are separated into train / validation / test sets
- Final-test customers/cards are completely unseen during training
- Same model family is used for Simple and History models
- Main metric: PR-AUC / Average Precision
- Secondary metrics: ROC-AUC, Precision, Recall, F1
- History groups: `0 | 1 | 2-3 | 4-5 | 6-10 | 11-20 | 21+`
- History features use only strictly past transactions
- Future-information leakage is blocked
- BankSim is tested across multiple customer splits
- Sparkov is used as a second-dataset validation

## Literature positioning

Existing research has already established several related points:

- historical customer behavior can improve fraud detection;
- low-frequency / low-history users are a known challenge;
- some prior studies explicitly vary sequence/history length or discuss minimum historical coverage;
- reported useful-history lengths differ substantially across datasets and modeling approaches.

Examples include work on low-frequency transaction fraud detection, individual behavior modeling, sequence-based fraud detection, and historical-coverage evaluation.

Therefore, the contribution of this repository is **not** “discovering that history helps.” Instead, it tests whether the history benefit and the apparent minimum useful-history point remain stable when:

1. Simple and History models are compared under the same algorithm;
2. test customers/cards are unseen during training;
3. future leakage is prevented;
4. performance is broken down by available history length;
5. multiple customer splits are tested;
6. the same idea is checked on a second dataset.

## Repository structure

```text
Customer-History-Fraud-Detection/
├── data/
│   ├── bs140513_032310.csv
│   └── README.md
├── experiments/
│   ├── banksim_history_experiment.py
│   └── sparkov_history_experiment.py
├── results/
├── docs/
│   ├── FINAL_RESEARCH_NOTE.md
│   ├── CROSS_DATASET_VALIDATION.md
│   └── PROFESSOR_PITCH.md
├── figures/
│   └── history_threshold.svg
├── requirements.txt
├── .gitignore
└── README.md
```

## Dataset

BankSim is included in this repository at:

```text
data/bs140513_032310.csv
```

Verified BankSim characteristics:

- 594,643 transactions
- 4,112 customers
- 7,200 fraud transactions
- `step` values covering days 0-179

Sparkov was used for external validation through the reproducible workflow.

## Install

```bash
pip install -r requirements.txt
```

## Run BankSim

```bash
python experiments/banksim_history_experiment.py \
  --csv data/bs140513_032310.csv \
  --output-dir results/banksim_history
```

## Main finding

Across BankSim and Sparkov, the History model outperformed the Simple model overall.

However, the exact history length at which the benefit became stable was **not the same across datasets**.

That means the strongest conclusion is not:

> “11 previous transactions are enough.”

Instead, it is:

> **Customer-specific history can improve fraud detection, but the amount of history required for a stable benefit appears to be dataset- and environment-dependent.**

This agrees with the broader literature, where reported useful-history lengths vary across methods and datasets.

## What this project adds

The project provides a controlled cross-dataset test of **history-benefit stability**, rather than claiming novelty for customer-history fraud detection itself.

Its main evidence comes from:

- unseen-customer/card evaluation;
- leakage-controlled history features;
- history-length groups;
- customer-level bootstrap uncertainty;
- repeated BankSim customer splits;
- Sparkov cross-dataset validation.

## Current status

The core experiments are complete.

The project is now positioned as a **controlled reproducibility / threshold-stability study** rather than as a claim that customer history has never been studied before.

For the complete methodology, literature positioning, results, cross-dataset validation, limitations, and future direction, see [docs/FINAL_RESEARCH_NOTE.md](docs/FINAL_RESEARCH_NOTE.md).
