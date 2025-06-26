import os
import cv2
import csv
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit
)


def jpeg_compression_attack(image, quality):
    """Compress and decompress image using JPEG at specified quality level."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, enc_img = cv2.imencode('.jpg', image, encode_param)
    return cv2.imdecode(enc_img, cv2.IMREAD_COLOR)


def test_jpeg_compression_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/jpeg_test_results",
    watermark: str = "qingquan",
    quality_range: list[int] = None
):
    if quality_range is None:
        quality_range = list(range(100, 0, -10))  # 100, 90, ..., 10

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

    # Save watermarked base
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    # CSV output
    csv_path = os.path.join(method_dir, f"{base_name}_jpeg_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "jpeg_quality", "decoded", "success", "attack_type", "can_decode_clean",
            "first_failure", "last_success"
        ])

        print(f"\nTesting JPEG compression robustness on {base_name} using {method}...")
        print(f"{'Quality':>8} | {'Decoded':<25} | Success")
        print("-" * 50)

        # CLEAN TEST
        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        status_clean = "✅" if success_clean else "❌"
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'CLEAN':>8} | {safe_decoded_clean:<25} | {status_clean}")
        writer.writerow([
            "clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""
        ])

        # TRACKING THRESHOLDS
        first_failure = None
        last_success = None

        for quality in quality_range:
            attacked = jpeg_compression_attack(watermarked, quality)
            out_name = f"jpeg_quality{quality}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{quality:8} | {safe_decoded:<25} | {status}")

            if success:
                last_success = quality
            elif first_failure is None:
                first_failure = quality

            writer.writerow([
                quality, safe_decoded, success, "jpeg", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])



def batch_test_jpeg_compression(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/jpeg_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_jpeg_compression_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )


# Example usage
if __name__ == "__main__":
    batch_test_jpeg_compression(methods=["dwtDct", "dwtDctSvd", "rivaGan"])
