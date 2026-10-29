# Phase 7 Control Report (constrained nonlinear MPC)

All arms share seeds, initial conditions, and limits. MPC predicts with
the correct plant model; only the sensing layer differs.

| arm | final P mean (g/L) | std | feed (L) | S RMSE | violations |
|---|---|---|---|---|---|
| assay | 9.736 | 9.097 | 36.26 | 0.023 | 252 |
| noisy_sigma0.005 | 9.126 | 8.392 | 35.414 | 0.028 | 202 |
| noisy_sigma0.02 | 8.892 | 8.066 | 35.422 | 0.028 | 201 |
| noisy_sigma0.05 | 9.22 | 7.41 | 36.082 | 0.029 | 225 |
| noisy_sigma0.1 | 10.025 | 6.363 | 37.022 | 0.029 | 223 |
| noisy_sigma0.2 | 10.554 | 4.623 | 36.228 | 0.031 | 182 |
| noisy_sigma0.5 | 8.476 | 2.481 | 25.686 | 0.04 | 36 |
| oracle | 9.154 | 8.431 | 35.416 | 0.028 | 207 |