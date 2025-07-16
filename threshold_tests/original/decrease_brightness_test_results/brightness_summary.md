# 📊 Brightness Threshold Summary

> 📘 **Brightness Decrease thresholds indicate the lowest brightness factor (0.0–1.0) where watermark decoding remained successful. Lower values show better robustness to dimming.**

This summary reports the robustness of each watermarking method under threshold-based attacks.
- **Clean Failures**: Number of images where the method failed to decode the original, unattacked watermarked image. These images are excluded from threshold calculations.
- **Attack Failures**: Number of images that failed decoding at all tested attack levels.
- **Threshold Statistics**: Calculated only from images that passed the clean test and at least one attack level. Includes average, median, standard deviation, minimum, and maximum threshold values observed.

| Method | Images | Clean Failures | Attack Failures | # Valid Thresholds | Avg Threshold | Median | Std Dev | Min | Max |
|--------|--------|----------------|------------------|---------------------|----------------|--------|---------|-----|-----|
| dwtDct | 15 | 2 | 2 | 13 | 0.80 | 0.80 | 0.14 | 0.40 | 1.00 |
| dwtDctSvd | 15 | 0 | 0 | 15 | 0.63 | 0.80 | 0.29 | 0.20 | 1.00 |

---
### dwtDct Threshold Distribution
![dwtDct Bar Graph](dwtDct_threshold_bar.png)

### dwtDctSvd Threshold Distribution
![dwtDctSvd Bar Graph](dwtDctSvd_threshold_bar.png)

## Combined Threshold Distribution
![Combined Threshold Bar Graph](brightness_combined_distribution.png)

