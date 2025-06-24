import os
import cv2

def center_crop_and_resize(image, size=(512, 512)):
    h, w = image.shape[:2]
    min_dim = min(h, w)
    # Calculate cropping box
    top = (h - min_dim) // 2
    left = (w - min_dim) // 2
    cropped = image[top:top + min_dim, left:left + min_dim]
    # Resize to target size
    return cv2.resize(cropped, size, interpolation=cv2.INTER_AREA)

def crop_and_resize_images_in_directory(
    input_root: str,
    output_root: str,
    target_size: tuple[int, int] = (512, 512)
):
    for subdir, _, files in os.walk(input_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                input_path = os.path.join(subdir, file)
                rel_path = os.path.relpath(input_path, input_root)
                output_path = os.path.join(output_root, rel_path)

                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                img = cv2.imread(input_path)
                if img is None:
                    print(f"❌ Failed to read image: {input_path}")
                    continue

                processed_img = center_crop_and_resize(img, target_size)
                cv2.imwrite(output_path, processed_img)
                print(f"✅ Cropped & resized: {output_path}")

# Define input and output paths
input_dir = "unsplash_test_set"
output_dir = "unsplash_test_set_resized"

crop_and_resize_images_in_directory(input_dir, output_dir)

