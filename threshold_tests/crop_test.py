import os
import cv2
import csv
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit
)


def crop_attack(image, crop_ratio):
    """Crop central region based on crop_ratio and resize to original dimensions."""
    h, w = image.shape[:2]
    crop_h = int(h * crop_ratio)
    crop_w = int(w * crop_ratio)
    start_y = (h - crop_h) // 2
    start_x = (w - crop_w) // 2
    cropped = image[start_y:start_y + crop_h, start_x:start_x + crop_w]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def test_crop_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/crop_test_results",
    watermark: str = "qingquan",
    crop_ratios: list[float] = None
):
    if crop_ratios is None:
        crop_ratios = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

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

    # CSV output
    csv_path = os.path.join(method_dir, f"{base_name}_crop_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "crop_ratio", "decoded", "success", "attack_type", "can_decode_clean",
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

        # Threshold tracking
        first_failure = None
        last_success = None

        for ratio in crop_ratios:
            attacked = crop_attack(watermarked, crop_ratio=ratio)
            out_name = f"crop_ratio_{ratio:.2f}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{ratio:8.2f} | {safe_decoded:<25} | {status}")

            if success:
                last_success = ratio
            elif first_failure is None:
                first_failure = ratio

            writer.writerow([
                ratio, safe_decoded, success, "crop", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])


def batch_test_crop_threshold(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/crop_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_crop_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )


# Example usage
if __name__ == "__main__":
    batch_test_crop_threshold(
        image_root="unsplash_test_set",
        methods=["dwtDct", "dwtDctSvd"],
        output_dir="threshold_tests/original/crop_test_results"
    )
