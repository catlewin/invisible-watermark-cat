import os
import cv2
import numpy as np
import csv
from watermark_utils import (
    embed_watermark_64bit,
    decode_watermark_64bit,
    embed_watermark_32bit,
    decode_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit,
    gaussian_noise_attack
)


def test_gaussian_noise_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/noise_test_results",
    watermark: str = "qingquan",
    noise_std_range: list[float] = None,
    early_stop_failures: int = 2
):
    if noise_std_range is None:
        noise_std_range = list(range(0, 51, 5))  # e.g., [0, 5, 10, ..., 50]

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Embed watermark
    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    # Extract base name and build output paths
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)

    # Save watermarked original
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    csv_path = os.path.join(method_dir, f"{base_name}_gaussian_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["std_dev", "decoded", "success"])

        print(f"\nTesting Gaussian noise robustness on {base_name} using {method}...")
        print(f"{'Std Dev':>8} | {'Decoded':<25} | Success")
        print("-" * 50)

        failure_streak = 0

        for std in noise_std_range:
            attacked = gaussian_noise_attack(watermarked, std=std)
            out_name = f"gaussian_std{std}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            print(f"{std:8} | {decoded[:25]:<25} | {status}")

            writer.writerow([std, decoded[:25], success])

            if not success:
                failure_streak += 1
                if failure_streak >= early_stop_failures:
                    print(f"Stopping early after {failure_streak} consecutive failures at std={std}")
                    break
            else:
                failure_streak = 0

def batch_test_gaussian_noise(
    image_root: str = "unsplash_test_set",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/noise_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]  # 32-bit for RivaGAN
                    test_gaussian_noise_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )

# Example usage:
batch_test_gaussian_noise(methods=["dwtDct"])

