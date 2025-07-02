# 🖼️ LPIPS Score at First Decode Failure — By Image

These plots show the **LPIPS score at the first decode failure for each image and each attack**, separated by method. This gives insight into:

- How individual images vary in robustness
- Which attacks cause failure earliest (lowest LPIPS) on specific images

These graphs help identify outlier images or attack-method pairs with inconsistent performance.


### dwtDct

![dwtDct — First Failure LPIPS](first_failure_lpips_plots/dwtDct_lpips_first_failure_by_image.png)

### dwtDctSvd

![dwtDctSvd — First Failure LPIPS](first_failure_lpips_plots/dwtDctSvd_lpips_first_failure_by_image.png)

### rivaGan

![rivaGan — First Failure LPIPS](first_failure_lpips_plots/rivaGan_lpips_first_failure_by_image.png)
