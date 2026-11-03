# History-group bootstrap reliability check

This check uses the current saved first-pass test predictions and resamples **customers**, not individual transactions, 1,000 times per history group.

Interpretation rule:
- CI entirely above 0: current split supports a reliable History-model gain.
- CI crossing 0: direction may be positive, but the group is not yet strong enough for a firm threshold claim.

Key findings:
- 0 previous: no benefit; CI crosses 0.
- 1 previous: no reliable benefit; very wide CI because only 26 frauds.
- 2–3 previous: +0.0324 PR-AUC; 95% CI [+0.0024, +0.0672] — reliable positive signal on this split.
- 4–5 previous: +0.0108; CI crosses 0.
- 6–10 previous: +0.0107; CI crosses 0 narrowly.
- 11–20 previous: +0.0203; 95% CI [+0.0029, +0.0372] — reliable positive signal.
- 21+ previous: +0.0401; 95% CI [+0.0231, +0.0513] — strong reliable positive signal.

Important: these intervals are computed from the current first-pass saved predictions. A final publication-level threshold claim should be checked across multiple customer splits, not inferred from one split alone.
