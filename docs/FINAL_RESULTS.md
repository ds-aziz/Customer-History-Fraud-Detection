# Final Experimental Summary

## Research question

**Does customer-specific past transaction behavior improve fraud detection when only a limited amount of customer history is available, and how much history is needed before the benefit becomes reliably reproducible?**

## Experimental setup

- Dataset: BankSim
- Total transactions: 594,643
- Customers: 4,112
- Fraud transactions: 7,200
- Train / validation / test split: customer-level
- Final-test customers are unseen during training
- Same model family is used for both comparisons
- Simple model: current transaction information only
- History model: same current transaction information + strictly past customer behavior
- Same-day leakage is blocked: only strictly earlier BankSim days are allowed in history features
- Primary metric: PR-AUC / Average Precision

## Overall result

The History model consistently outperformed the Simple model.

In the detailed confirmatory run:

| Model | PR-AUC | Recall | F1 |
|---|---:|---:|---:|
| Simple | 0.8942 | 0.8077 | 0.8251 |
| History | **0.9370** | **0.8615** | **0.8586** |

**PR-AUC improvement: +0.0428**

A customer-level bootstrap check supported a positive overall gain.

## Robustness across customer splits

Five different unseen-customer splits were tested.

| Seed | Simple PR-AUC | History PR-AUC | Gain |
|---:|---:|---:|---:|
| 11 | 0.8923 | 0.9201 | +0.0279 |
| 22 | 0.8941 | 0.9260 | +0.0319 |
| 33 | 0.8898 | 0.9374 | +0.0477 |
| 44 | 0.8909 | 0.9231 | +0.0321 |
| 55 | 0.8871 | 0.9211 | +0.0340 |

The History model was better in **5/5 splits**.

Mean PR-AUC gain across these splits: **+0.0347**.

## How much customer history is needed?

The multi-seed history-group screen gave the following pattern:

| Previous transactions | Positive splits | Mean PR-AUC gain | Interpretation |
|---|---:|---:|---|
| 0 | 0/5 | -0.0299 | No benefit |
| 1 | 4/5 | +0.0147 | Unstable |
| 2–3 | 3/5 | +0.0033 | Unstable |
| 4–5 | 4/5 | +0.0069 | Unstable |
| 6–10 | 4/5 | +0.0196 | Mostly positive, not fully stable |
| **11–20** | **5/5** | **+0.0238** | **Consistently positive** |
| **21+** | **5/5** | **+0.0520** | **Strong consistently positive** |

## Main conclusion

> On BankSim, customer-specific transaction history improves fraud detection overall. Very short histories (roughly 1–10 previous transactions) can help, but the effect is not stable across customer splits. The earliest consistently reproducible benefit appears once a customer has roughly **11 or more previous transactions**.

This is a **BankSim-specific experimental finding**, not a universal banking threshold.

## Why this result matters

The result suggests that the usefulness of personalized customer behavior is not simply binary ("history helps" vs "history does not help"). Its value depends on how much past behavior is available.

For new or low-history customers, a fraud model may need to rely more heavily on current-transaction and population-level information. As history accumulates, customer-specific behavioral features become increasingly reliable.

## Current project status

The core research question has been answered experimentally on BankSim.

Remaining work is presentation and validation work rather than a change in research direction:

1. preserve the experiment and results reproducibly;
2. present the result clearly for professors / scholarship applications;
3. optionally validate the same idea on a second dataset later as external validation.
