# ai_upscale_test.py
import os
import cv2
import csv
from watermark_utils import (
    safe_decode_watermark,
    safe_decode_watermark_32bit
)

def test_ai_upscale_attack(
    image_path: str,
    base_name: str,
    method: str,
    output_dir: str,
    watermark: str = "qingquan"
):
    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Choose correct decode function
    if method == "rivaGan":
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        safe_decode_fn = safe_decode_watermark

    # Setup output folder and CSV
    method_dir = os.path.join(output_dir, method)
    os.makedirs(method_dir, exist_ok=True)
    csv_path = os.path.join(method_dir, f"{base_name}_ai_upscale_results.csv")

    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(["attack_type", "decoded", "success", "filename"])

        print(f"\nTesting AI UPSCALE robustness on {base_name} using {method}...")
        decoded, success = safe_decode_fn(img, watermark, method)
        status = "✅" if success else "❌"
        safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'UPSCALE':>8} | {safe_decoded:<25} | {status}")

        writer.writerow([
            "ai_upscale", safe_decoded, success, os.path.basename(image_path)
        ])


def batch_test_ai_upscale_attack(
    root_dir: str = "threshold_tests/512x512_all_methods_results/ai_upscale_results",
    methods: list[str] = ["dwtDct"],
    watermark: str = "qingquan"
):
    for method in methods:
        method_dir = os.path.join(root_dir, method)
        for base_name in os.listdir(method_dir):
            image_dir = os.path.join(method_dir, base_name)
            img_path = os.path.join(image_dir, "upscalemedia-transformed.jpeg")
            if not os.path.isfile(img_path):
                continue
            wm = watermark if method != "rivaGan" else watermark[:4]
            test_ai_upscale_attack(
                image_path=img_path,
                base_name=base_name,
                method=method,
                output_dir=os.path.join(root_dir),
                watermark=wm
            )


# Example usage
if __name__ == "__main__":
    batch_test_ai_upscale_attack()
