# Noise Threshold Summary

This summary includes average, median, and standard deviation of Gaussian Noise (σ) thresholds at which watermark decoding failed.

| Method | Images | Failures | Avg Threshold | Median | Std Dev | Min | Max |
|--------|--------|----------|----------------|--------|---------|-----|-----|
| dwtDct | 15 | 11 | 3.75 | 2.50 | 4.15 | 0 | 10 |
| dwtDctSvd | 15 | 0 | 12.67 | 15.00 | 2.49 | 10 | 15 |
| rivaGan | 15 | 1 | 19.64 | 20.00 | 8.55 | 5 | 35 |

---
### dwtDct Threshold Distribution
![dwtDct Bar Graph](dwtDct_threshold_bar.png)

### dwtDctSvd Threshold Distribution
![dwtDctSvd Bar Graph](dwtDctSvd_threshold_bar.png)

### rivaGan Threshold Distribution
![rivaGan Bar Graph](rivaGan_threshold_bar.png)

## Combined Threshold Distribution
![Combined Threshold Bar Graph](noise_combined_distribution.png)

