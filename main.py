import os
import cv2
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit,
    run_watermark_tests,
    jpeg_compression_attack,
    resize_attack,
    gaussian_noise_attack,
    crop_attack,
    brightness_attack,
    overlay_with_smiley,
    mask_attack,
    rotate_attack
)

# === Load original image
img = cv2.imread("test_vectors/original.jpg")

# === Output directory
output_dir = "attacked_images"
os.makedirs(output_dir, exist_ok=True)

# === Define watermark strings
watermark_64bit = "qingquan"  # 64 bits
watermark_32bit = "qing"      # 32 bits (required for rivaGan)

# === Define attack functions
attack_tests = {
    "No Attack": lambda x: x.copy(),
    "JPEG Compression (Q=40)": lambda x: jpeg_compression_attack(x, quality=40),
    "Resize (50%)": lambda x: resize_attack(x, scale=0.5),
    "Gaussian Noise (std=5)": lambda x: gaussian_noise_attack(x, std=5),
    "Crop (7x5%)": lambda x: crop_attack(x, crop_percent_h=0.07, crop_percent_w=0.05),
    "Brightness x1.2": lambda x: brightness_attack(x, factor=1.2),
    "Overlay (Smiley)": lambda x: overlay_with_smiley(x),
    "Mask (20%)": lambda x: mask_attack(x, mask_fraction=0.2),
    "Rotate (30°)": lambda x: rotate_attack(x, angle=30),
}

# === Define watermarking methods
methods = {
    "dwtDct": {
        "embed_fn": lambda img: embed_watermark_64bit(img, watermark_64bit, method="dwtDct"),
        "decode_fn": lambda img: safe_decode_watermark(img, expected_text=watermark_64bit, method="dwtDct"),
    },
    "dwtDctSvd": {
        "embed_fn": lambda img: embed_watermark_64bit(img, watermark_64bit, method="dwtDctSvd"),
        "decode_fn": lambda img: safe_decode_watermark(img, expected_text=watermark_64bit, method="dwtDctSvd"),
    },
    "rivaGan": {
        "embed_fn": lambda img: embed_watermark_32bit(img, watermark_32bit, method="rivaGan"),
        "decode_fn": lambda img: safe_decode_watermark_32bit(img, expected_text=watermark_32bit, method="rivaGan"),
    },
}

# === Run tests for each method
for method_name, method_cfg in methods.items():
    print(f"\n🔬 Running tests for method: {method_name}")
    run_watermark_tests(
        method_name=method_name,
        image=img,
        embed_fn=method_cfg["embed_fn"],
        decode_fn=method_cfg["decode_fn"],
        attacks=attack_tests,
        output_dir=output_dir
    )
