# Cross-Dataset Validation: BankSim vs Sparkov

## Same research question

Does customer-specific past transaction behavior improve fraud detection, and how much history is needed before the benefit becomes useful?

The same Simple-vs-History idea was tested on Sparkov after the BankSim experiment.

## Sparkov overall result

Test set:
- 161,882 transactions
- 142 unseen cards
- 948 fraud transactions

| Model | PR-AUC | Recall | F1 |
|---|---:|---:|---:|
| Simple | 0.5813 | 0.6055 | 0.6199 |
| History | **0.8225** | **0.7194** | **0.7781** |

PR-AUC gain: **+0.2412**

Customer-level bootstrap (300 replicates):
- mean gain: **+0.2401**
- 95% CI: **+0.2100 to +0.2716**

This strongly supports the broad finding that past customer/card behavior can improve fraud detection.

## History-length groups on Sparkov

| Previous transactions | PR-AUC gain |
|---|---:|
| 0 | -0.0816 |
| 1 | -0.0112 |
| 2-3 | +0.0293 |
| 4-5 | +0.1158 |
| 6-10 | +0.0428 |
| 11-20 | -0.0403 |
| 21+ | +0.2544 |

Important caveat: some early/mid-history groups contain very few fraud examples. For example, the 11-20 group has only 12 fraud cases in this test split, so its negative point estimate should not be treated as a stable threshold result.

## Cross-dataset interpretation

What **did replicate**:
- zero/very-short history is not reliably helpful;
- adding customer/card history improves overall fraud detection;
- mature history can provide a large benefit.

What **did not replicate exactly**:
- BankSim's approximate "11+ previous transactions" threshold did not appear as the same clean cutoff on Sparkov.

Therefore the stronger research conclusion is:

> The value of customer-specific history is real and reproducible across these two synthetic transaction datasets, but the exact amount of history needed before the benefit becomes stable is dataset-dependent.

This is more scientifically defensible than claiming that 11 transactions is a universal threshold.

## Limitation

BankSim and Sparkov are both synthetic/simulated datasets. This validation shows that the effect is not unique to one simulator, but it is still not equivalent to validation on real bank transaction data.
