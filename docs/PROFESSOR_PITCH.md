# Professor Pitch

## 30-second version

I am studying a simple but important fraud-detection question:

**How much customer transaction history is actually needed before personalized behavior becomes useful?**

Using the BankSim dataset, I compared two fraud models under the same conditions:

- a **Simple model** using only the current transaction;
- a **History model** using the same current transaction plus strictly past customer behavior.

To keep the test fair, final-test customers were unseen during training and same-day leakage was blocked.

The History model consistently performed better overall. Across multiple unseen-customer splits, the benefit was unstable when only 1-10 previous transactions were available, but it became consistently reproducible from roughly **11 or more previous transactions**. The strongest gains appeared for customers with 21+ previous transactions.

So the main finding is not only that history helps, but that **the amount of available history matters**.

## 60-second version

My project focuses on a cold-start problem in fraud detection.

Many fraud systems can use a customer's past behavior, but new customers do not have much history. So I asked:

**At what point does customer-specific transaction history become reliably useful for fraud detection?**

I tested this on BankSim using two models with the same algorithm. The baseline model only received the current transaction. The second model received the same information plus customer-history features built only from strictly earlier days.

I used customer-level train, validation, and test splits, so final-test customers were completely unseen during training. This avoids the model simply memorizing customers.

The History model improved overall PR-AUC, recall, and F1. More importantly, when I separated results by how much previous history was available, short histories were unstable across different customer splits. The first range that showed a positive gain in all tested splits was **11-20 previous transactions**, while 21+ transactions showed the strongest improvement.

This suggests that personalized behavioral history can improve fraud detection, but its value depends on how much reliable past behavior is available.

## Why this may be research-useful

The contribution is not a new fraud model architecture. The focus is the **measurement problem**:

> When does customer history become reliable enough to help?

This can be useful when thinking about fraud detection for new or low-history customers, where a system may need to rely more on population-level or current-transaction signals until enough personal history accumulates.

## Current limitation

This threshold is a **BankSim-specific experimental result**, not a universal banking rule. The next stronger validation would be to test the same question on another suitable dataset without changing the core research question.
