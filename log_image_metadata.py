import os
from PIL import Image
import csv

def log_image_metadata(input_dir, output_csv):
    image_data = []

    for root, _, files in os.walk(input_dir):
        for fname in files:
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                fpath = os.path.join(root, fname)
                try:
                    with Image.open(fpath) as img:
                        width, height = img.size
                        file_size_kb = os.path.getsize(fpath) / 1024
                        image_data.append({
                            "filename": fname,
                            "width": width,
                            "height": height,
                            "resolution": f"{width}x{height}",
                            "file_size_kb": round(file_size_kb, 2),
                            "format": img.format
                        })
                except Exception as e:
                    print(f"Failed to open {fname}: {e}")

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=image_data[0].keys())
        writer.writeheader()
        writer.writerows(image_data)

    print(f"Metadata logged to {output_csv}")

# Example usage:
log_image_metadata("unsplash_test_set", "image_metadata.csv")
