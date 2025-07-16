import os
import cv2
import numpy as np
import csv
from PIL import Image, ImageEnhance
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit,
)

def brightness_attack(image: np.ndarray, factor: float) -> np.ndarray:
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    enhancer = ImageEnhance.Brightness(pil_img)
    bright_img = enhancer.enhance(factor)
    return cv2.cvtColor(np.array(bright_img), cv2.COLOR_RGB2BGR)

def test_brightness_decrease_threshold(
    image_path: str,
    method: str,
    output_dir: str = "threshold_tests/decrease_brightness_test_results",
    watermark: str = "qingquan",
    brightness_range: list[float] = None,
):
    if brightness_range is None:
        brightness_range = [1.0, 0.8, 0.6, 0.4, 0.2]  # up to and including 1.0

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Embed watermark
    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    # Output directories
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)

    # Save watermarked original
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    # CSV output
    csv_path = os.path.join(method_dir, f"{base_name}_decrease_brightness_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "brightness_factor", "decoded", "success", "attack_type", "can_decode_clean",
            "first_failure", "last_success"
        ])

        print(f"\nTesting Brightness Decrease on {base_name} using {method}...")
        print(f"{'Brightness':>10} | {'Decoded':<25} | Success")
        print("-" * 60)

        # Clean test
        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'clean':>10} | {safe_decoded_clean:<25} | {'✅' if success_clean else '❌'}")
        writer.writerow([
            "clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""
        ])

        first_failure = None
        last_success = None

        for factor in brightness_range:
            attacked = brightness_attack(watermarked, factor)
            out_name = f"brightness_{factor:.2f}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{factor:10.2f} | {safe_decoded:<25} | {status}")

            if success:
                last_success = factor
            elif first_failure is None:
                first_failure = factor

            writer.writerow([
                factor, safe_decoded, success, "brightness", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])

def batch_test_brightness_decrease(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/decrease_brightness_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_brightness_decrease_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )

if __name__ == "__main__":
    batch_test_brightness_decrease(
        image_root="unsplash_test_set",
        methods=["dwtDct", "dwtDctSvd"],
        output_dir="threshold_tests/original/decrease_brightness_test_results"
    )
