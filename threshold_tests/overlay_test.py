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


def overlay_attack(base_image, overlay_image, alpha):
    """Overlay a semi-transparent image on top of base_image."""
    overlay_resized = cv2.resize(overlay_image, (base_image.shape[1], base_image.shape[0]))
    return cv2.addWeighted(overlay_resized, alpha, base_image, 1 - alpha, 0)


def test_overlay_threshold(
    image_path: str,
    overlay_path: str = "threshold_tests/overlay_logo.png",
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/overlay_test_results",
    watermark: str = "qingquan",
    alpha_range: list[float] = None
):
    if alpha_range is None:
        alpha_range = [round(x, 2) for x in np.arange(0.0, 1.05, 0.1)]  # alpha 0.0 to 1.0

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    overlay_img = cv2.imread(overlay_path)
    assert overlay_img is not None, f"Failed to load overlay image: {overlay_path}"

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

    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    # CSV
    csv_path = os.path.join(method_dir, f"{base_name}_overlay_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "alpha", "decoded", "success", "attack_type", "can_decode_clean", "first_failure", "last_success"
        ])

        print(f"\nTesting Overlay attack on {base_name} using {method}...")
        print(f"{'Alpha':>6} | {'Decoded':<25} | Success")
        print("-" * 50)

        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'CLEAN':>6} | {safe_decoded_clean:<25} | {'✅' if success_clean else '❌'}")
        writer.writerow(["clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""])

        first_failure = None
        last_success = None

        for alpha in alpha_range:
            attacked = overlay_attack(watermarked, overlay_img, alpha)
            out_name = f"overlay_alpha{alpha:.2f}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            status = "✅" if success else "❌"
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            print(f"{alpha:6.2f} | {safe_decoded:<25} | {status}")

            if success:
                last_success = alpha
            elif first_failure is None:
                first_failure = alpha

            writer.writerow([
                alpha, safe_decoded, success, "overlay", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])


def batch_test_overlay(
    image_root: str = "unsplash_test_set_resized",
    overlay_path: str = "threshold_tests/overlay_logo.png",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/overlay_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_overlay_threshold(
                        image_path=image_path,
                        overlay_path=overlay_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )


# Example usage
if __name__ == "__main__":
    batch_test_overlay(methods=["dwtDct", "dwtDctSvd", "rivaGan"])
