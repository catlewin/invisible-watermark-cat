import os
import cv2
import csv
from watermark_utils import (
    embed_watermark_64bit,
    embed_watermark_32bit,
    safe_decode_watermark,
    safe_decode_watermark_32bit
)


def rotate_image(image, angle):
    """Rotate image around center without cropping."""
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return rotated


def test_rotate_threshold(
    image_path: str,
    method: str = "dwtDct",
    output_dir: str = "threshold_tests/rotate_test_results",
    watermark: str = "qingquan",
    angle_range: list[int] = None
):
    if angle_range is None:
        angle_range = list(range(0, 20, 2))  # 0 to 18 degrees

    img = cv2.imread(image_path)
    assert img is not None, f"Failed to load image: {image_path}"

    # Embed watermark
    if method == "rivaGan":
        watermarked = embed_watermark_32bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark_32bit
    else:
        watermarked = embed_watermark_64bit(img, watermark, method)
        safe_decode_fn = safe_decode_watermark

    # Output paths
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    method_dir = os.path.join(output_dir, method)
    image_dir = os.path.join(method_dir, base_name)
    os.makedirs(image_dir, exist_ok=True)

    cv2.imwrite(os.path.join(image_dir, "original_watermarked.jpg"), watermarked)

    # CSV output
    csv_path = os.path.join(method_dir, f"{base_name}_rotate_results.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f, escapechar='\\', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([
            "angle", "decoded", "success", "attack_type", "can_decode_clean", "first_failure", "last_success"
        ])

        print(f"\nTesting Rotation robustness on {base_name} using {method}...")
        print(f"{'Angle':>8} | {'Decoded':<25} | Success")
        print("-" * 50)

        decoded_clean, success_clean = safe_decode_fn(watermarked, watermark, method)
        safe_decoded_clean = decoded_clean[:25].encode("utf-8", "replace").decode("utf-8")
        print(f"{'CLEAN':>8} | {safe_decoded_clean:<25} | {'✅' if success_clean else '❌'}")
        writer.writerow(["clean", safe_decoded_clean, success_clean, "clean", success_clean, "", ""])

        first_failure = None
        last_success = None

        for angle in angle_range:
            attacked = rotate_image(watermarked, angle)
            out_name = f"rotate_{angle}.jpg"
            cv2.imwrite(os.path.join(image_dir, out_name), attacked)

            decoded, success = safe_decode_fn(attacked, watermark, method)
            safe_decoded = decoded[:25].encode("utf-8", "replace").decode("utf-8")
            status = "✅" if success else "❌"
            print(f"{angle:8} | {safe_decoded:<25} | {status}")

            if success:
                last_success = angle
            elif first_failure is None:
                first_failure = angle

            writer.writerow([
                angle, safe_decoded, success, "rotate", success_clean,
                first_failure if first_failure is not None else "",
                last_success if last_success is not None else ""
            ])


def batch_test_rotate(
    image_root: str = "unsplash_test_set_resized",
    methods: list[str] = ["dwtDct", "dwtDctSvd", "rivaGan"],
    output_dir: str = "threshold_tests/rotate_test_results",
    watermark: str = "qingquan"
):
    for root, _, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                for method in methods:
                    wm = watermark if method != "rivaGan" else watermark[:4]
                    test_rotate_threshold(
                        image_path=image_path,
                        method=method,
                        output_dir=output_dir,
                        watermark=wm
                    )


if __name__ == "__main__":
    batch_test_rotate(
        image_root="unsplash_test_set",
        methods=["dwtDct", "dwtDctSvd"],
        output_dir="threshold_tests/original_img_dwt_methods_results/rotate_test_results"
    )
