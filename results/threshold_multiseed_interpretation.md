# Multi-seed history-threshold robustness check

Purpose: verify whether the History-model gain repeats within each history-length group across five different unseen-customer splits.

Settings:
- Seeds: 11, 22, 33, 44, 55
- Same customer-level 70/15/15 split logic
- Same Simple vs History feature definitions
- Same strictly-earlier-day leakage rule
- 40 CatBoost iterations per model for this robustness screen (used to test direction consistency, not final absolute performance)

## Summary

| History group | Positive splits | Mean PR-AUC gain | Minimum gain | Interpretation |
|---|---:|---:|---:|---|
| 0 | 0/5 | -0.0299 | -0.0443 | Consistently no benefit |
| 1 | 4/5 | +0.0147 | -0.0150 | Unstable |
| 2-3 | 3/5 | +0.0033 | -0.0223 | Unstable |
| 4-5 | 4/5 | +0.0069 | -0.0137 | Unstable |
| 6-10 | 4/5 | +0.0196 | -0.0066 | Mostly positive, not fully stable |
| 11-20 | 5/5 | +0.0238 | +0.0080 | Consistently positive |
| 21+ | 5/5 | +0.0520 | +0.0211 | Strong consistently positive |

## Interpretation

The earlier single-split result suggested a possible positive signal as early as 2-3 previous transactions. Across multiple customer splits, however, the early groups (1 through 10 previous transactions) are not stable enough to support a firm minimum-history threshold.

The first group with a positive History-model gain in all five splits is **11-20 previous transactions**. The 21+ group is also positive in all five splits and shows the largest average gain.

Therefore, the current robust conclusion is:

> Customer history improves BankSim fraud detection overall, but the earliest consistently reproducible benefit appears once customers have roughly **11 or more previous transactions**.

This should be treated as the current robust experimental threshold, not as a universal banking rule.
