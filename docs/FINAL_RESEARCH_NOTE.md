# Final Research Note

## Title

**When Does Customer Transaction History Become Useful for Fraud Detection? A Controlled Study on BankSim and Sparkov**

## 1. Research problem

Fraud-detection systems often benefit from customer-specific behavioral information. However, a practical difficulty appears for new or low-history customers: very little past behavior is available.

This project studies a focused question:

> **Does customer-specific past transaction behavior improve fraud detection, and how much previous history is needed before that benefit becomes reliable?**

The aim is not to invent a new fraud-detection algorithm. The aim is to measure when personalized customer history becomes useful.

---

## 2. Core experimental idea

Two fraud-detection models are compared under the same conditions.

### Simple Model

Uses information from the current transaction only.

### History Model

Uses the same current-transaction information plus features derived from the customer's strictly past transactions.

The same CatBoost model family is used for both models. This keeps the comparison controlled: the main difference between the two systems is the presence or absence of customer-history information.

---

## 3. History features

The History Model uses behavioral summaries such as:

- number of previous transactions;
- previous average transaction amount;
- previous transaction amount variability;
- previous maximum transaction amount;
- recent previous transaction behavior;
- current amount relative to the customer's previous average;
- whether any prior customer history is available.

Previous fraud labels are not used as customer-history features.

---

## 4. Leakage control

A central requirement of the experiment is that no future information may be used.

For every transaction, history features are created only from earlier transactions.

### BankSim

BankSim provides day-level ordering. Therefore, a transaction on day *t* may use only information from days strictly earlier than *t*. Transactions from the same day are not treated as ordered history.

### Sparkov

Sparkov provides transaction timestamps / ordering, so history is built from strictly earlier transactions for the same card.

This prevents future-information leakage from artificially improving the History Model.

---

## 5. Customer-level evaluation

The datasets are split by customer/card rather than by individual transaction.

This means final-test customers/cards are unseen during model training.

The purpose is to test whether the approach works on new customers rather than simply memorizing customers already present in the training set.

The approximate split is:

- 70% customers/cards: training
- 15%: validation
- 15%: final test

---

## 6. Main evaluation metric

The primary metric is **PR-AUC / Average Precision**.

Fraud is rare compared with normal transactions, so ordinary accuracy can be misleading. PR-AUC focuses more directly on performance for the minority fraud class.

Secondary metrics include:

- ROC-AUC
- Precision
- Recall
- F1 score

---

# 7. BankSim experiment

BankSim contains:

- **594,643 transactions**
- **4,112 customers**
- **7,200 fraud transactions**

The detailed confirmatory test used completely unseen final-test customers.

## Overall BankSim result

| Model | PR-AUC | Recall | F1 |
|---|---:|---:|---:|
| Simple Model | 0.8942 | 0.8077 | 0.8251 |
| History Model | **0.9370** | **0.8615** | **0.8586** |

The History Model improved PR-AUC by approximately:

**+0.0428**

A customer-level bootstrap analysis produced a positive confidence interval, supporting the conclusion that the overall gain was unlikely to be only a random split effect.

---

## 8. BankSim robustness across multiple customer splits

Five different customer splits were tested.

| Seed | Simple PR-AUC | History PR-AUC | Gain |
|---:|---:|---:|---:|
| 11 | 0.8923 | 0.9201 | +0.0279 |
| 22 | 0.8941 | 0.9260 | +0.0319 |
| 33 | 0.8898 | 0.9374 | +0.0477 |
| 44 | 0.8909 | 0.9231 | +0.0321 |
| 55 | 0.8871 | 0.9211 | +0.0340 |

The History Model was better in **5 out of 5 splits**.

Mean PR-AUC gain across these runs:

**approximately +0.0347**

This showed that the overall effect was not limited to a single lucky customer split.

---

# 9. How much history was needed on BankSim?

Transactions were grouped according to the amount of previous customer history available:

- 0
- 1
- 2–3
- 4–5
- 6–10
- 11–20
- 21+

Across multiple customer splits, the pattern was:

| Previous transactions | Positive splits | Mean PR-AUC gain | Interpretation |
|---|---:|---:|---|
| 0 | 0/5 | -0.0299 | No benefit |
| 1 | 4/5 | +0.0147 | Unstable |
| 2–3 | 3/5 | +0.0033 | Unstable |
| 4–5 | 4/5 | +0.0069 | Unstable |
| 6–10 | 4/5 | +0.0196 | Mostly positive but not fully stable |
| 11–20 | 5/5 | +0.0238 | Consistently positive |
| 21+ | 5/5 | +0.0520 | Strong consistently positive |

On BankSim, the first history range that produced a positive gain in all five tested splits was **11–20 previous transactions**.

However, this was treated as a dataset-specific observation rather than a universal rule.

---

# 10. External validation on Sparkov

A second dataset was used to check whether the broad finding was specific to BankSim.

Sparkov provides repeated card-level transactions with:

- card identifier;
- transaction ordering/time;
- transaction amount;
- merchant/category information;
- fraud labels.

The same Simple-vs-History research question was tested.

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

This strongly supported the broad finding that customer/card history can improve fraud detection.

---

# 11. Sparkov history-length pattern

The history-group results on Sparkov were:

| Previous transactions | PR-AUC gain |
|---|---:|
| 0 | -0.0816 |
| 1 | -0.0112 |
| 2–3 | +0.0293 |
| 4–5 | +0.1158 |
| 6–10 | +0.0428 |
| 11–20 | -0.0403 |
| 21+ | +0.2544 |

Some early/mid-history groups contained very few fraud examples, so individual threshold estimates were unstable.

Most importantly, the exact BankSim threshold did **not** reproduce identically on Sparkov.

---

# 12. Main cross-dataset finding

The strongest conclusion from the two datasets is:

> **Customer-specific transaction history improves fraud detection overall, but the amount of history required before the benefit becomes stable is dataset-dependent.**

What repeated across both datasets:

- zero or extremely short history was not reliably useful;
- personalized history improved overall fraud detection;
- mature customer/card history could provide strong gains.

What did not repeat exactly:

- the exact minimum number of previous transactions required for reliable improvement.

Therefore, the project does **not** claim that “11 transactions” is a universal fraud-detection threshold.

Instead, the broader finding is:

> **The value of personalized customer history depends on how much reliable past behavior is available.**

---

# 13. Interpretation

The result can be understood through a simple behavioral example.

Suppose a transaction amount is unusually large.

Without customer history, the model only knows that the transaction is large.

With sufficient customer history, the model can compare the transaction against the customer's normal spending pattern.

For a customer who usually spends small amounts, a very large transaction may be highly unusual.

For another customer who regularly makes large purchases, the same transaction may be normal.

However, if only one or two previous transactions are available, the estimated “normal behavior” of the customer may be unreliable.

As more transactions accumulate, the customer's behavioral baseline becomes more informative.

---

# 14. Contribution of the project

The contribution is not a new machine-learning architecture.

The contribution is a controlled measurement question:

> **When does customer-specific transaction history become useful enough to improve fraud detection?**

The project contributes:

1. a controlled Simple-vs-History comparison;
2. customer-level unseen evaluation;
3. strict prevention of future-information leakage;
4. evaluation by history length;
5. bootstrap uncertainty analysis;
6. robustness testing across multiple customer splits;
7. validation on a second transaction dataset.

---

# 15. Limitations

The main limitations are:

### Synthetic datasets

Both BankSim and Sparkov are simulated/synthetic transaction datasets.

Therefore, the findings should not be presented as guaranteed behavior in real banking systems.

### Dataset-dependent threshold

The exact amount of history required before the benefit becomes stable differed between datasets.

This suggests that the threshold may depend on:

- transaction patterns;
- customer behavior;
- fraud generation process;
- available features;
- dataset size and fraud prevalence.

### Small early-history fraud counts

Some history groups contain relatively few fraud examples, making precise threshold estimation difficult.

---

# 16. Final conclusion

This project started with a simple question:

> **Does customer history help fraud detection, and how much history is needed?**

The experiments showed that customer-specific history can substantially improve fraud detection.

On BankSim, the improvement was positive across multiple unseen-customer splits, with more stable gains appearing once a meaningful amount of customer history had accumulated.

On Sparkov, the overall improvement was even larger, confirming that the broad effect was not unique to BankSim.

However, the exact minimum-history threshold differed between datasets.

The most defensible conclusion is:

> **Personalized transaction history is valuable for fraud detection, but its usefulness depends on the amount and reliability of past customer behavior. The exact point at which history becomes reliably useful is dataset-dependent.**

This provides a clear basis for future work using real transaction data or more realistic fraud settings.
