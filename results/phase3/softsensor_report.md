# Phase 3 Soft-Sensor Report

- Features: feed_rate_l_h, agitator_rpm, temperature_k, ph, do2_mg_l, volume_l, co2_out_pct, o2_out_pct
- Train batches: 72 (plus 10 deviation batches held out)
- Held-out batches: 28

| model | split | MAE | RMSE | R2 |
|---|---|---|---|---|
| ridge | pooled | 4.625 | 6.824 | 0.516 |
| ridge | normal_test | 4.241 | 6.004 | 0.647 |
| ridge | fault_test | 5.296 | 8.058 | 0.145 |
| random_forest | pooled | 2.480 | 4.133 | 0.823 |
| random_forest | normal_test | 2.129 | 3.875 | 0.853 |
| random_forest | fault_test | 3.092 | 4.549 | 0.727 |

Published baselines (different splits, quoted for context only):
- Acosta-Pavas 2024 Cubist: R2 0.908, RMSE 3.149, MAE 1.920.
- Metcalfe 2025 LSTM on deviation batches 94, 99, 100: MAE 2.39 to 2.68 g/L.