import os
import cv2
import csv
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit
)


def embed_images(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/512x512_all_methods_results/upscale_test_results",
    watermark: str = "qingquan"
):
    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Embed watermark
    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    # Output setup
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)


    csv_path = os.path.join(method_dir, f"{base_name}_upscale_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "upscale", "decoded", "success", "attack_type", "can_decode_clean",
            "first_failure", "last_success"
        ])

        print(f"\nTesting CROP robustness on {base_name} using {method}...")
        print(f"{'Crop %':>8} | {'Decoded':<25} | Success")
        print("-" * 50)

        # Clean decode
        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        status_clean = "✅" if success_clean else "❌"
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'CLEAN':>8} | {safe_decoded_clean:<25} | {status_clean}")
        writer.writerow([
            "clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""
        ])

def batch_embed(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/512x512_all_methods_results/upscale_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    embed_images(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )

def decode_upscaled_images(
    input_root: str = "threshold_tests/512x512_all_methods_results/upscale_test_results",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    watermark: str = "qingquan"
):
    for method in methods:
        method_dir = os.path.join(input_root, method)
        if not os.path.isdir(method_dir):
            continue

        for image_name in os.listdir(method_dir):
            image_dir = os.path.join(method_dir, image_name)
            if not os.path.isdir(image_dir):
                continue

            attacked_path = os.path.join(image_dir, "rescaled.jpg")
            if not os.path.exists(attacked_path):
                print(f"❌ Missing rescaled image for {method}/{image_name}")
                continue

            img = cv2.imread(attacked_path)
            if img is None:
                print(f"❌ Failed to load image: {attacked_path}")
                continue

            wm = watermark if method != "rivaGan" else watermark[:4]
            decode_fn = safe_decode_watermark if method != "rivaGan" else safe_decode_watermark_32bit

            decoded, success = decode_fn(img, wm, method)
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            status = "✅" if success else "❌"

            print(f"{method}/{image_name}: {safe_decoded} | {status}")

            # Append result to CSV
            csv_path = os.path.join(method_dir, f"{image_name}_upscale_results.csv")
            with open(csv_path, mode="a", newline="") as f:
                writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow([
                    "upscale",          # upscale ratio
                    safe_decoded,      # decoded string (truncated + safe)
                    success,           # success boolean
                    "upscale",         # attack type
                    "",                # can_decode_clean (already logged earlier)
                    "",                # first_failure
                    ""                 # last_success
                ])

# Example usage
if __name__ == "__main__":
    '''
    batch_embed(
        image_root="unsplash_test_set_resized",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        output_dir="threshold_tests/512x512_all_methods_results/upscale_test_results"
    )
    '''
    decode_upscaled_images()

