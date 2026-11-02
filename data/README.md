# BankSim data

Place the raw BankSim transaction file here locally as:

```text
data/bs140513_032310.csv
```

The raw CSV is intentionally excluded from Git so that the repository stays lightweight and reproducible.

Expected file:

- Filename: `bs140513_032310.csv`
- Transactions: 594,643
- Unique customers: 4,112
- Fraud transactions: 7,200

The experiment script validates the required BankSim columns before training.
