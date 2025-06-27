import os
import cv2
import csv
import numpy as np
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit
)


def apply_mask_attack(image, mask_fraction):
    """Apply a black rectangular mask covering a percentage of the image."""
    h, w = image.shape[:2]
    mask_area = int(h * w * mask_fraction)
    side = int(np.sqrt(mask_area))

    start_x = w // 2 - side // 2
    start_y = h // 2 - side // 2

    masked_image = image.copy()
    masked_image[start_y:start_y + side, start_x:start_x + side] = 0
    return masked_image


def test_mask_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/mask_test_results",
    watermark: str = "qingquan",
    mask_range: list[float] = None
):
    if mask_range is None:
        mask_range = [round(x, 2) for x in np.arange(0.0, 1.05, 0.05)]

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    csv_path = os.path.join(method_dir, f"{base_name}_mask_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "mask_fraction", "decoded", "success", "attack_type", "can_decode_clean",
            "first_failure", "last_success"
        ])

        print(f"\nTesting mask robustness on {base_name} using {method}...")
        print(f"{'Fraction':>8} | {'Decoded':<25} | Success")
        print("-" * 50)

        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        status_clean = "✅" if success_clean else "❌"
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'CLEAN':>8} | {safe_decoded_clean:<25} | {status_clean}")
        writer.writerow([
            "clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""
        ])

        first_failure = None
        last_success = None

        for frac in mask_range:
            attacked = apply_mask_attack(watermarked, frac)
            out_name = f"mask_frac{int(frac * 100)}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{frac:8.2f} | {safe_decoded:<25} | {status}")

            if success:
                last_success = frac
            elif first_failure is None:
                first_failure = frac

            writer.writerow([
                frac, safe_decoded, success, "mask", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])


def batch_test_mask_attack(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/mask_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_mask_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )


if __name__ == "__main__":
    batch_test_mask_attack(methods=["dwtDct", "dwtDctSvd", "rivaGan"])
