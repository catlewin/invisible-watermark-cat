import os
import cv2
import csv
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit
)


def resize_attack(image, scale):
    """Downscale and then upscale image by a given scale factor."""
    h, w = image.shape[:2]
    resized = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    restored = cv2.resize(resized, (w, h), interpolation=cv2.INTER_LINEAR)
    return restored


def test_resize_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/resize_test_results",
    watermark: str = "qingquan",
    scale_factors: list[float] = None
):
    if scale_factors is None:
        scale_factors = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Embed watermark
    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    # Output dirs
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)
    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    # CSV setup
    csv_path = os.path.join(method_dir, f"{base_name}_resize_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "scale", "decoded", "success", "attack_type", "can_decode_clean",
            "first_failure", "last_success"
        ])

        print(f"\nTesting Resize robustness on {base_name} using {method}...")
        print(f"{'Scale':>6} | {'Decoded':<25} | Success")
        print("-" * 50)

        # CLEAN DECODE
        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'CLEAN':>6} | {safe_decoded_clean:<25} | {'✅' if success_clean else '❌'}")
        writer.writerow([
            "clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""
        ])

        # Track thresholds
        first_failure = None
        last_success = None

        for scale in scale_factors:
            attacked = resize_attack(watermarked, scale)
            out_name = f"resize_scale{scale:.2f}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{scale:6.2f} | {safe_decoded:<25} | {status}")

            if success:
                last_success = scale
            elif first_failure is None:
                first_failure = scale

            writer.writerow([
                scale, safe_decoded, success, "resize", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])


def batch_test_resize(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/resize_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_resize_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )


if __name__ == "__main__":
    batch_test_resize(
        image_root="unsplash_test_set",
        methods=["dwtDct", "dwtDctSvd"],
        output_dir="threshold_tests/original/resize_test_results"
    )
