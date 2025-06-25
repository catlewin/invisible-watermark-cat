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
    """Apply brightness adjustment using PIL for better fidelity."""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    enhancer = ImageEnhance.Brightness(pil_img)
    bright_img = enhancer.enhance(factor)
    return cv2.cvtColor(np.array(bright_img), cv2.COLOR_RGB2BGR)

def test_brightness_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/brightness_test_results",
    watermark: str = "qingquan",
    brightness_range: list[float] = None,
):
    if brightness_range is None:
        brightness_range = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Embed watermark
    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    # Prepare output directories
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)

    # Save watermarked original
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    # CSV result path
    csv_path = os.path.join(method_dir, f"{base_name}_brightness_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(["brightness_factor", "decoded", "success"])

        print(f"\nTesting Brightness robustness on {base_name} using {method}...")
        print(f"{'Brightness':>10} | {'Decoded':<25} | Success")
        print("-" * 50)

        # For brightness, we test both darkening and brightening, so no early stopping

        for factor in brightness_range:
            attacked = brightness_attack(watermarked, factor)
            out_name = f"brightness_{factor:.2f}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{factor:10.2f} | {safe_decoded:<25} | {status}")

            writer.writerow([factor, safe_decoded, success])


def batch_test_brightness_threshold(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/brightness_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_brightness_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )

# Example usage:
if __name__ == "__main__":
    batch_test_brightness_threshold(methods=["dwtDct", "dwtDctSvd", "rivaGan"])
