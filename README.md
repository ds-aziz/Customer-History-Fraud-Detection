# Customer-History-Fraud-Detection

Research experiment on whether limited customer transaction history improves fraud detection using the BankSim dataset.

## Research question

Does customer-specific past transaction behavior improve fraud detection when only a small amount of customer history is available?

The experiment compares two models using the same algorithm:

- **Simple model:** current transaction information only
- **History model:** the same current transaction information plus strictly past customer behavior

The goal is not only to ask whether history helps, but also **how much prior history is needed before the benefit becomes meaningful**.

## Experimental design

- Dataset: BankSim
- Split: customers are separated into train / validation / test sets
- Final-test customers are completely unseen during training
- Same algorithm is used for both models
- Main metric: PR-AUC / Average Precision
- Secondary metrics: ROC-AUC, Precision, Recall, F1
- History groups: `0 | 1 | 2-3 | 4-5 | 6-10 | 11-20 | 21+`
- Leakage rule: a transaction may only use information from strictly earlier days
- Same-day transactions are not treated as ordered history because BankSim provides day-level timestamps only

## Repository structure

```text
Customer-History-Fraud-Detection/
├── data/
│   ├── bs140513_032310.csv
│   └── README.md
├── experiments/
│   └── banksim_history_experiment.py
├── results/
│   └── .gitkeep
├── requirements.txt
├── .gitignore
└── README.md
```

## Dataset

The verified BankSim CSV is included in this repository at:

```text
data/bs140513_032310.csv
```

Verified characteristics:

- 594,643 transactions
- 4,112 customers
- 7,200 fraud transactions
- `step` values covering days 0-179

The import workflow validates these counts before committing the dataset.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python experiments/banksim_history_experiment.py \
  --csv data/bs140513_032310.csv \
  --output-dir results/banksim_history
```

The script saves:

- overall Simple vs History metrics
- history-group results
- test-set predictions
- trained CatBoost models
- customer-level bootstrap confidence interval for PR-AUC difference


## Main finding

Across unseen-customer tests, the History model consistently outperformed the Simple model overall. In the robustness screen, the first history-length group with a positive gain in all five customer splits was **11–20 previous transactions**; the **21+** group showed the strongest average gain.

See the full experimental summary in [docs/FINAL_RESULTS.md](docs/FINAL_RESULTS.md) and the threshold figure in [figures/history_threshold.svg](figures/history_threshold.svg).

## Current status

Dataset, experiment design, and implementation are now in the repository. The next step is to run the locked experiment and inspect the measured improvement by available customer-history length.
