# Final Research Note

## Title

**How Stable Is the Benefit of Customer Transaction History for Fraud Detection? A Controlled Cross-Dataset Study on BankSim and Sparkov**

## 1. Research problem

Fraud-detection research has long used customer-specific historical behavior. Prior work has already shown that previous transactions can improve fraud detection, and the difficulty of profiling low-frequency or low-history users is also well known.

Therefore, this project does **not** claim that “customer history helps fraud detection” is a new discovery.

The narrower question studied here is:

> **Is there a stable or universal point at which customer-specific transaction history becomes reliably useful for fraud detection, or does that point depend on the dataset and transaction environment?**

The aim is to measure the **stability and reproducibility** of the history benefit under a controlled protocol.

---

## 2. Positioning against prior work

Several lines of prior research are directly relevant.

### Historical behavior is already established

Previous fraud-detection systems have compared current activity against a customer's past behavior, built customer behavioral profiles, or learned sequential representations from historical transactions.

### Low-history / low-frequency users are already a known problem

Prior studies have explicitly addressed users with few historical transactions. For example, low-frequency transaction methods and behavior-profiling approaches try to supplement sparse personal history with group or contextual information.

### History length has also been studied before

Some sequence-based and behavior-based fraud studies vary the amount of available transaction history, use explicit sequence lengths, or discuss how much historical coverage is needed.

Reported useful-history lengths differ substantially between studies and datasets. This means it is not scientifically safe to claim that a single universal number of prior transactions is already established.

### Gap targeted by this project

The gap examined here is narrower:

> **When a current-transaction-only model and a history-augmented model are compared under the same algorithm, with unseen-customer evaluation and leakage control, how stable is the history benefit across history lengths, random customer splits, and different datasets?**

This is the contribution tested in this repository.

---

## 3. Core experimental idea

Two fraud-detection models are compared under the same conditions.

### Simple Model

Uses information from the current transaction only.

### History Model

Uses the same current-transaction information plus features derived from the customer's strictly past transactions.

The same CatBoost model family is used for both models. This keeps the comparison controlled: the main experimental difference is the presence or absence of customer-history information.

---

## 4. History features

The History Model uses behavioral summaries such as:

- number of previous transactions;
- previous average transaction amount;
- previous transaction amount variability;
- previous maximum transaction amount;
- recent previous transaction behavior;
- current amount relative to the customer's previous average;
- whether prior customer history exists.

Previous fraud labels are not used as history features.

---

## 5. Leakage control

For every transaction, history features are created only from earlier transactions.

### BankSim

BankSim provides day-level ordering. Therefore, a transaction on day *t* may use only information from days strictly earlier than *t*. Same-day transactions are not treated as ordered history.

### Sparkov

Sparkov provides transaction ordering/timestamps, so history is built only from earlier transactions for the same card.

This prevents future-information leakage from artificially improving the History Model.

---

## 6. Unseen-customer/card evaluation

The datasets are split by customer/card rather than by individual transaction.

Approximate split:

- 70% customers/cards: training
- 15%: validation
- 15%: final test

Final-test identities are completely unseen during training.

This makes the evaluation stricter than a random transaction split and reduces the chance that performance is driven by memorizing customer identities.

---

## 7. Evaluation metrics

Primary metric:

- **PR-AUC / Average Precision**

Secondary metrics:

- ROC-AUC
- Precision
- Recall
- F1

PR-AUC is emphasized because fraud is highly imbalanced.

---

# 8. BankSim experiment

BankSim contains:

- **594,643 transactions**
- **4,112 customers**
- **7,200 fraud transactions**

## Overall BankSim result

| Model | PR-AUC | Recall | F1 |
|---|---:|---:|---:|
| Simple Model | 0.8942 | 0.8077 | 0.8251 |
| History Model | **0.9370** | **0.8615** | **0.8586** |

PR-AUC gain:

**+0.0428**

A customer-level bootstrap analysis supported a positive overall difference.

---

## 9. BankSim robustness across customer splits

Five different unseen-customer splits were tested.

| Seed | Simple PR-AUC | History PR-AUC | Gain |
|---:|---:|---:|---:|
| 11 | 0.8923 | 0.9201 | +0.0279 |
| 22 | 0.8941 | 0.9260 | +0.0319 |
| 33 | 0.8898 | 0.9374 | +0.0477 |
| 44 | 0.8909 | 0.9231 | +0.0321 |
| 55 | 0.8871 | 0.9211 | +0.0340 |

The History Model was better in **5/5 splits**.

Mean PR-AUC gain:

**approximately +0.0347**

This supports the stability of the **overall** history benefit on BankSim.

---

# 10. BankSim history-length pattern

Transactions were grouped by available previous history:

- 0
- 1
- 2–3
- 4–5
- 6–10
- 11–20
- 21+

Across multiple customer splits:

| Previous transactions | Positive splits | Mean PR-AUC gain | Interpretation |
|---|---:|---:|---|
| 0 | 0/5 | -0.0299 | No benefit |
| 1 | 4/5 | +0.0147 | Unstable |
| 2–3 | 3/5 | +0.0033 | Unstable |
| 4–5 | 4/5 | +0.0069 | Unstable |
| 6–10 | 4/5 | +0.0196 | Mostly positive but not fully stable |
| 11–20 | 5/5 | +0.0238 | Consistently positive |
| 21+ | 5/5 | +0.0520 | Strong consistently positive |

On BankSim, the first range with a positive gain in all five tested splits was **11–20 previous transactions**.

This is treated only as a **BankSim-specific observation**, not as a universal threshold.

---

# 11. Sparkov cross-dataset validation

Sparkov was used to test whether the broad pattern was unique to BankSim.

The Sparkov run used:

- **1,048,575 transactions**
- **943 cards**
- **6,006 fraud transactions**

Final test set:

- **161,882 transactions**
- **142 unseen cards**
- **948 fraud transactions**

## Overall Sparkov result

| Model | PR-AUC | Recall | F1 |
|---|---:|---:|---:|
| Simple Model | 0.5813 | 0.6055 | 0.6199 |
| History Model | **0.8225** | **0.7194** | **0.7781** |

PR-AUC gain:

**+0.2412**

Customer-level bootstrap:

- mean gain: **+0.2401**
- 95% CI: **+0.2100 to +0.2716**

The broad history benefit therefore replicated strongly on a second dataset.

---

# 12. Sparkov history-length pattern

| Previous transactions | PR-AUC gain |
|---|---:|
| 0 | -0.0816 |
| 1 | -0.0112 |
| 2–3 | +0.0293 |
| 4–5 | +0.1158 |
| 6–10 | +0.0428 |
| 11–20 | -0.0403 |
| 21+ | +0.2544 |

Some early/mid-history groups contain very few fraud examples, making their individual estimates unstable.

Most importantly, the exact BankSim transition point did **not** reproduce identically on Sparkov.

---

# 13. Main cross-dataset result

What replicated:

- the History Model improved overall fraud detection;
- zero or very short history was not reliably useful;
- mature history could provide strong gains.

What did **not** replicate exactly:

- one fixed minimum number of previous transactions at which the gain becomes stable.

Therefore:

> **Customer-specific transaction history can improve fraud detection, but the amount of history required for stable benefit appears to depend on the dataset, transaction environment, and modeling setup.**

This is the central result of the project.

---

# 14. What is and is not novel here

## Not claimed as novel

This project does **not** claim novelty for:

- using customer history in fraud detection;
- behavioral profiling;
- recognizing low-history users as difficult;
- the general idea that sequence/history length can affect performance.

These ideas exist in prior research.

## Contribution tested here

The project contributes a controlled empirical study combining:

1. a same-algorithm Simple-vs-History comparison;
2. unseen-customer/card evaluation;
3. strict leakage control;
4. performance broken down by available history length;
5. bootstrap uncertainty;
6. repeated customer splits;
7. cross-dataset validation.

The main contribution is therefore about **stability, reproducibility, and generalizability of the history benefit**, not about discovering historical behavior as a new fraud signal.

---

# 15. Interpretation

A customer's behavioral baseline becomes more informative as more transactions accumulate.

But the amount of history required to build a useful baseline can differ because datasets differ in:

- customer behavior;
- transaction frequency;
- fraud prevalence;
- fraud-generation process;
- available features;
- simulator or data-collection design;
- model architecture and training protocol.

This explains why one universal history cutoff is unlikely to transfer unchanged across all fraud settings.

---

# 16. Limitations

### Both datasets are synthetic

BankSim and Sparkov are simulated datasets. Cross-dataset replication is useful, but it is not equivalent to real-bank validation.

### Exact threshold remains uncertain

The exact transition point differed between datasets and some early-history groups contained few fraud cases.

### Literature already contains related history-length work

Because prior work has already studied low-frequency users and history/sequence length, this project must be presented as a controlled reproducibility/stability study rather than as the first work on history sufficiency.

---

# 17. Future research direction

The strongest next research question is:

> **How stable is the benefit of customer-specific transaction history across different transaction environments, model families, and real-world datasets, and which factors determine the amount of history required before personalization becomes reliable?**

Potential future work:

- real bank or payment-platform transaction data;
- additional datasets with clear customer identity and temporal ordering;
- different model families;
- formal learning-curve analysis over history length;
- cold-start strategies that combine personal and population-level behavior;
- studying why the useful-history point shifts between datasets.

---

# 18. Final conclusion

Prior literature already shows that customer history can help fraud detection.

This project's main result is narrower:

> **The history benefit is reproducible overall, but the point at which it becomes reliably useful is not stable across datasets.**

BankSim and Sparkov both showed clear overall gains from customer-specific history, but they did not support one identical minimum-history threshold.

Therefore, the most defensible conclusion is:

> **There is no evidence here for a universal fixed transaction-history threshold. The amount of history needed for reliable personalization appears to be dataset- and environment-dependent.**

That is the final scientific framing of this project.
