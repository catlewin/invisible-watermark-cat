import os
import argparse
from perceptual_model import lpips
import torch
from PIL import Image
from torchvision import transforms
import pandas as pd

# Initialize LPIPS model
loss_fn = lpips.LPIPS(net='alex')

# Transform: resize + normalize
transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])


def load_image(path):
    return transform(Image.open(path).convert("RGB")).unsqueeze(0)


def calculate_lpips_scores(image_dir, output_csv):
    clean_image_path = os.path.join(image_dir, "original_watermarked.jpg")
    if not os.path.exists(clean_image_path):
        raise FileNotFoundError(f"Missing clean reference image at: {clean_image_path}")

    print(f"Using clean reference image: {clean_image_path}")
    clean_img = load_image(clean_image_path)

    results = [("filename", "lpips_score")]

    for fname in sorted(os.listdir(image_dir)):
        if not fname.lower().endswith((".jpg", ".png")):
            continue
        if fname == "original_watermarked.jpg":
            continue

        attacked_path = os.path.join(image_dir, fname)
        attacked_img = load_image(attacked_path)

        score = loss_fn(clean_img, attacked_img).item()
        results.append((fname, score))
        print(f"{fname}: {score:.4f}")

    # Save results
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df = pd.DataFrame(results[1:], columns=["filename", "lpips_score"])
    df.to_csv(output_csv, index=False)
    print(f"\n✅ Saved LPIPS scores to: {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate LPIPS scores for brightness attack images.")
    parser.add_argument("--dir", required=True,
                        help="Directory containing original_watermarked.jpg and brightness_*.jpg files")
    parser.add_argument("--output_csv", required=True, help="Output CSV path for LPIPS scores")
    args = parser.parse_args()

    calculate_lpips_scores(args.dir, args.output_csv)
