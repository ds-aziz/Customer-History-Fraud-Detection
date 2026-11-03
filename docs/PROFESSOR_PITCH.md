# Professor Pitch

## 30-second version

Prior research already shows that customer transaction history can improve fraud detection, so my project does not treat that as a new discovery.

My question is narrower:

**Is there a stable amount of customer history after which personalization becomes reliably useful, or is that point dataset-dependent?**

I tested this using the same Simple-vs-History comparison under unseen-customer evaluation and strict leakage control. On BankSim and Sparkov, customer history improved fraud detection overall, but the exact minimum useful-history point did not reproduce across datasets.

So the main result is that **the history benefit is real, but the amount of history required for stable benefit appears to depend on the transaction environment**.

## 60-second version

My project studies a cold-start and generalization problem in fraud detection.

Previous research already uses historical customer behavior and has also studied low-frequency users, so I do not claim that customer history itself is novel.

Instead, I ask:

**How stable is the benefit of customer-specific transaction history across different amounts of available history and across datasets?**

I compare two models using the same algorithm: a Simple model with current-transaction information only, and a History model with the same information plus strictly past customer behavior.

The evaluation is customer/card-level, so final-test identities are unseen during training, and future-information leakage is blocked.

On BankSim, the History model improved PR-AUC across multiple customer splits. On Sparkov, the overall improvement was even larger. However, the exact point at which history became consistently useful was not the same across the two datasets.

That suggests there may not be a universal fixed history threshold. The more interesting research problem is understanding **why the required history length changes across datasets, transaction environments, and models**.

## Research contribution

The contribution is not a new fraud-model architecture and not the discovery that historical behavior can help.

The contribution is a controlled empirical protocol for examining the **stability and generalizability of the history benefit**, using:

- same-algorithm Simple-vs-History comparison;
- unseen-customer/card evaluation;
- strict leakage prevention;
- history-length groups;
- bootstrap uncertainty;
- repeated customer splits;
- cross-dataset validation.

## Literature-aware positioning

Prior work has already studied:

- customer behavioral profiling;
- historical transaction sequences;
- low-frequency / low-history users;
- sequence/history length effects.

Reported useful-history lengths differ between studies and datasets.

My current result is therefore best interpreted as evidence that **the useful-history point is not necessarily universal**.

## Current limitation and MS direction

BankSim and Sparkov are both synthetic datasets.

A stronger MS-level continuation would test the same controlled question on real transaction data and investigate which factors determine how much customer history is needed before personalized fraud detection becomes reliable.
