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
    # Paths to clean and attacked images
    clean_path = os.path.join(os.path.dirname(image_path), "original_watermarked.jpg")
    assert os.path.isfile(clean_path), f"Missing clean image: {clean_path}"
    assert os.path.isfile(image_path), f"Missing upscaled image: {image_path}"

    clean_img = cv2.imread(clean_path)
    attacked_img = cv2.imread(image_path)
    assert clean_img is not None, f"Failed to load image: {clean_path}"
    assert attacked_img is not None, f"Failed to load image: {image_path}"

    # Choose decode function
    if method == "rivaGan":
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        safe_decode_fn = safe_decode_watermark

    # Output path
    method_dir = os.path.join(output_dir, method)
    os.makedirs(method_dir, exist_ok=True)
    csv_path = os.path.join(method_dir, f"{base_name}_ai_upscale_results.csv")

    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(["attack_type", "decoded", "success", "filename"])

        print(f"\nTesting AI UPSCALE robustness on {base_name} using {method}...")

        # Decode clean image
        decoded_clean, success_clean = safe_decode_fn(clean_img, watermark, method)
        status_clean = "✅" if success_clean else "❌"
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'CLEAN':>8} | {safe_decoded_clean:<25} | {status_clean}")
        writer.writerow(["clean", safe_decoded_clean, success_clean, os.path.basename(clean_path)])

        # Decode upscaled image
        decoded_upscaled, success_upscaled = safe_decode_fn(attacked_img, watermark, method)
        status_upscaled = "✅" if success_upscaled else "❌"
        safe_decoded_upscaled = decoded_upscaled[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'UPSCALE':>8} | {safe_decoded_upscaled:<25} | {status_upscaled}")
        writer.writerow(["ai_upscale", safe_decoded_upscaled, success_upscaled, os.path.basename(image_path)])



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
