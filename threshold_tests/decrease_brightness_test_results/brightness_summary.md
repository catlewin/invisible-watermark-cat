# 📊 Brightness Threshold Summary

This summary reports the robustness of each watermarking method under threshold-based attacks.
- **Clean Failures**: Number of images where the method failed to decode the original, unattacked watermarked image. These images are excluded from threshold calculations.
- **Attack Failures**: Number of images that failed decoding at all tested attack levels.
- **Threshold Statistics**: Calculated only from images that passed the clean test and at least one attack level. Includes average, median, standard deviation, minimum, and maximum threshold values observed.

| Method | Images | Clean Failures | Attack Failures | # Valid Thresholds | Avg Threshold | Median | Std Dev | Min | Max |
|--------|--------|----------------|------------------|---------------------|----------------|--------|---------|-----|-----|
| dwtDct | 15 | 11 | 11 | 4 | 0.90 | 0.90 | 0.10 | 0.80 | 1.00 |
| dwtDctSvd | 15 | 0 | 0 | 15 | 0.99 | 1.00 | 0.05 | 0.80 | 1.00 |
| rivaGan | 15 | 1 | 1 | 14 | 0.59 | 0.60 | 0.16 | 0.40 | 0.80 |

---
### dwtDct Threshold Distribution
![dwtDct Bar Graph](dwtDct_threshold_bar.png)

### dwtDctSvd Threshold Distribution
![dwtDctSvd Bar Graph](dwtDctSvd_threshold_bar.png)

### rivaGan Threshold Distribution
![rivaGan Bar Graph](rivaGan_threshold_bar.png)

## Combined Threshold Distribution
![Combined Threshold Bar Graph](brightness_combined_distribution.png)

