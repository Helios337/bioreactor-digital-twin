# Phase 6 Control Report (rule-based feed, matched arms)

All arms share seeds, initial conditions, and operating limits. Process noise sigma = 0.01.

| arm | final P mean (g/L) | std | feed (L) | S RMSE | violations |
|---|---|---|---|---|---|
| recipe | 10.89 | 0.871 | 17.6 | 0.024 | 19 |
| noisy_sigma0.005 | 7.392 | 3.132 | 24.07 | 0.129 | 35 |
| oracle | 7.363 | 3.462 | 23.976 | 0.13 | 34 |
| noisy_sigma0.02 | 6.619 | 3.014 | 22.728 | 0.133 | 36 |
| noisy_sigma0.1 | 6.615 | 1.734 | 22.094 | 0.135 | 38 |
| noisy_sigma0.05 | 6.319 | 2.276 | 21.672 | 0.138 | 34 |
| noisy_sigma0.5 | 6.284 | 1.905 | 21.644 | 0.147 | 34 |
| noisy_sigma0.2 | 6.022 | 1.791 | 21.258 | 0.14 | 39 |
| assay | 0.01 | 0.001 | 3.8 | 1.662 | 0 |

Reading (reviewer interpretation, to be revisited by the MPC arm):
- Online substrate feedback (oracle or soft-sensor-like) far outperforms
  the delayed 12 h plus 4 h assay feedback, which collapses the batch
  (final P near zero).
- Final penicillin is only modestly sensitive to the estimator noise
  level over a broad range (sigma 0.005 to 0.5), so this PI design is
  robust to soft-sensor error.
- The tuned constant-feed recipe outperforms this substrate-PI at the
  chosen setpoint, which is a humility result consistent with simpler
  designs winning in earlier literature.