# BankSim data

The verified BankSim transaction dataset is included here as:

```text
data/bs140513_032310.csv
```

Verified file characteristics:

- Filename: `bs140513_032310.csv`
- Transactions: 594,643
- Unique customers: 4,112
- Fraud transactions: 7,200

The repository's import workflow downloads the BankSim CSV from the public `prinz-nussknacker/banksim1` mirror and validates the expected row, customer, and fraud counts before committing it.

The experiment script also validates the required BankSim columns before training.
