import os
import cv2
import csv
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit,
    gaussian_noise_attack
)


def test_gaussian_noise_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/noise_test_results",
    watermark: str = "qingquan",
    noise_std_range: list[float] = None
):
    if noise_std_range is None:
        noise_std_range = list(range(0, 36, 5))  # [0, 5, ..., 50]

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Embed watermark
    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    # Output paths
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    # CSV setup
    csv_path = os.path.join(method_dir, f"{base_name}_gaussian_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "std_dev", "decoded", "success", "attack_type", "can_decode_clean",
            "first_failure", "last_success"
        ])

        print(f"\nTesting Gaussian noise robustness on {base_name} using {method}...")
        print(f"{'Std Dev':>8} | {'Decoded':<25} | Success")
        print("-" * 60)

        # Clean decode (no attack)
        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'clean':>8} | {safe_decoded_clean:<25} | {'✅' if success_clean else '❌'}")
        writer.writerow([
            "clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""
        ])

        # Track thresholds
        first_failure = None
        last_success = None

        for std in noise_std_range:
            attacked = gaussian_noise_attack(watermarked, std=std)
            out_name = f"gaussian_std{std}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{std:8} | {safe_decoded:<25} | {status}")

            if success:
                last_success = std
            elif first_failure is None:
                first_failure = std

            writer.writerow([
                std, safe_decoded, success, "noise", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])


def batch_test_gaussian_noise(
    image_root: str = "unsplash_test_set_resized",
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
batch_test_gaussian_noise(
    image_root="unsplash_test_set",
    methods=["dwtDct", "dwtDctSvd"],
    output_dir="threshold_tests/original/noise_test_results"
)

