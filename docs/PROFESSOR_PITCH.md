# Professor Pitch

## 30-second version

I am studying a focused fraud-detection question:

**When does customer-specific transaction history become useful enough to improve fraud detection?**

I compare two models under the same conditions: a **Simple model** using only the current transaction, and a **History model** using the same current information plus strictly past customer behavior.

On BankSim, the History model improved fraud detection across multiple unseen-customer splits. I then repeated the same idea on Sparkov, where the overall improvement was even larger.

The broad result replicated across both datasets: **customer history helps**, but the exact amount of history needed before the benefit becomes stable is **dataset-dependent**.

## 60-second version

My project focuses on a cold-start problem in fraud detection.

Fraud models can benefit from a customer's past behavior, but new customers have very little history. So I asked:

**How much previous transaction history is needed before personalized behavior becomes reliably useful?**

I tested this using a controlled Simple-vs-History design. Both models used the same algorithm. The baseline model received only current-transaction information. The second model received the same information plus features derived strictly from previous customer transactions.

I used customer/card-level train, validation, and test splits, so final-test identities were unseen during training. I also blocked future-information leakage and evaluated performance by available history length.

On BankSim, the History model improved overall PR-AUC across multiple customer splits. I then repeated the same research question on Sparkov, where the History model again produced a substantial overall improvement.

The exact minimum useful-history threshold was not identical across the two datasets. That led to the stronger conclusion that **personalized transaction history is useful, but the point at which it becomes stable depends on the transaction environment and dataset**.

## Why this may be research-useful

The contribution is not a new fraud-model architecture. The focus is the **measurement problem**:

> When does customer history become reliable enough to help?

This is relevant to fraud detection for new or low-history customers, where a system may need to rely more on current-transaction and population-level information until enough individual behavior has accumulated.

## Current limitation

Both BankSim and Sparkov are synthetic datasets. The next stronger step would be validation using real transaction data or a more realistic dataset, while keeping the same core research question.
