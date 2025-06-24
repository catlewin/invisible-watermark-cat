# 🔬 Watermark Robustness Test Summary

This table summarizes the decoding results for each attack across the three watermarking methods: `dwtDct`, `dwtDctSvd`, and `rivaGan`.

| **Attack**              | **Image**                                                                    | **dwtDct**                | **dwtDctSvd**                | **rivaGan**       |
| ----------------------- |------------------------------------------------------------------------------| ------------------------- | ---------------------------- | ----------------- |
| No Attack               | ![No Attack](attacked_images/dwtDct/No_Attack.jpg)                           | ✅ `qingquan`              | ✅ `qingquan`                 | ✅ `qing`          |
| JPEG Compression (Q=40) | ![JPEG Compression (Q=40)](attacked_images/dwtDct/JPEG_Compression_Q_40.jpg) | ❌ `\x00\x00\x00\x00@\x00` | ❌ `P\x00\x00\x03 0 $`        | ✅ `qing`          |
| Resize (50%)            | ![Resize (50%)](attacked_images/dwtDct/Resize_50_.jpg)                       | ✅ `qingquan`              | ✅ `qingquan`                 | ✅ `qing`          |
| Gaussian Noise (std=5)  | ![Gaussian Noise (std=5)](attacked_images/dwtDct/Gaussian_Noise_std_5.jpg)   | ✅ `qingquan`              | ✅ `qingquan`                 | ✅ `qing`          |
| Crop (7x5%)             | ![Crop (7x5%)](attacked_images/dwtDct/Crop_7x5_.jpg)                         | ❌ `[UTF-8 Error]`         | ❌ `[UTF-8 Error]`            | ✅ `qing`          |
| Brightness x1.2         | ![Brightness x1.2](attacked_images/dwtDct/Brightness_x1.2.jpg)               | ✅ `qingquan`              | ❌ `[UTF-8 Error]`            | ✅ `qing`          |
| Overlay (Smiley)        | ![Overlay (Smiley)](attacked_images/dwtDct/Overlay_Smiley.jpg)               | ✅ `qingquan`              | ✅ `qingquan`                 | ✅ `qing`          |
| Mask (20%)              | ![Mask (20%)](attacked_images/dwtDct/Mask_20_.jpg)                           | ✅ `qingquan`              | ✅ `qingquan`                 | ✅ `qing`          |
| Rotate (30°)            | ![Rotate (30°)](attacked_images/dwtDct/Rotate_30.jpg)                        | ❌ `[UTF-8 Error]`         | ❌ `\x00\x00\x00\x00\x00\x02` | ❌ `[UTF-8 Error]` |

Legend:

* ✅: Exact match with expected watermark.
* ❌: Failure or decoding error.
* UTF-8 Error indicates corrupted or malformed decoding.

> Note: `rivaGan` only supports 32-bit watermarks, which is why its decoded string is shorter (`qing` instead of `qingquan`).
