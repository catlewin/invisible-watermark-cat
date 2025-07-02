# 🔁 Average LPIPS vs Semantic Severity

These plots show the **average LPIPS score vs. semantic severity** for each attack type, grouped by method. Semantic severity is a normalized representation of how extreme the attack is, ranging from 0 (minimal attack) to 1 (maximum threshold tested).

This analysis answers: *At what semantic severity do watermark decodes begin to become too visually perceptible?*

### dwtDct

![dwtDct](avg_lpips_vs_semantic_severity/avg_lpips_vs_semantic_severity_dwtDct.png)

### dwtDctSvd

![dwtDctSvd](avg_lpips_vs_semantic_severity/avg_lpips_vs_semantic_severity_dwtDctSvd.png)

### rivaGan

![rivaGan](avg_lpips_vs_semantic_severity/avg_lpips_vs_semantic_severity_rivaGan.png)
