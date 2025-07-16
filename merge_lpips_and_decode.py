import os
import pandas as pd
import re

def extract_threshold_from_filename(filename, attack):
    """
    Extracts numeric threshold for merging LPIPS and decode results.
    Handles attack-specific filename formats:
    - mask: 'mask_frac25.jpg' → 0.25
    - others: 'crop_ratio_0.40.jpg' → 0.40
    """
    if attack == "mask":
        match = re.search(r"mask_frac(\d+)", filename)
        if match:
            return float(match.group(1)) / 100
    else:
        match = re.search(r'([0-9]+\.[0-9]+)(?=\.jpg$|\.png$)', filename)
        if match:
            return float(match.group(1))
    return None


def merge_lpips_and_decode(lpips_base_dir, decode_base_dir, output_base_dir, attack, methods, image_names):
    binary_attacks = ["upscale", "denoising"]

    for method in methods:
        for image in image_names:
            # Define file paths
            lpips_csv = os.path.join(
                lpips_base_dir, f"{attack}_test_results", "original", method, f"{image}_lpips_scores.csv"
            )
            decode_csv = os.path.join(
                decode_base_dir, f"{attack}_test_results", method,
                f"{image}_gaussian_results.csv" if attack == "noise" else f"{image}_{attack}_results.csv"
            )
            output_csv = os.path.join(
                output_base_dir, f"{attack}_test_results", "original", method, f"{image}_merged_results.csv"
            )

            if not os.path.exists(lpips_csv) or not os.path.exists(decode_csv):
                print(f"⚠️ Missing file(s): {lpips_csv} or {decode_csv}")
                continue

            df_lpips = pd.read_csv(lpips_csv)
            df_decode = pd.read_csv(decode_csv)

            decode_key = df_decode.columns[0]

            # Handle binary attacks differently (no thresholds)
            if attack in binary_attacks:
                df_lpips["attack_type"] = df_lpips["filename"].apply(lambda f: "clean" if "original_watermarked" in f else attack)
                merged_df = pd.merge(
                    df_decode,
                    df_lpips[["attack_type", "lpips_score"]],
                    on="attack_type",
                    how="left"
                )
            else:
                # Parse and normalize thresholds
                df_lpips["threshold"] = df_lpips["filename"].apply(lambda f: extract_threshold_from_filename(f, attack))
                df_lpips["threshold"] = pd.to_numeric(df_lpips["threshold"], errors='coerce').round(3)

                df_clean = df_decode[df_decode[decode_key] == "clean"]
                df_attacked = df_decode[df_decode[decode_key] != "clean"].copy()
                df_attacked[decode_key] = pd.to_numeric(df_attacked[decode_key], errors='coerce').round(3)

                # Merge on threshold
                merged_attacked = pd.merge(
                    df_attacked,
                    df_lpips[["threshold", "lpips_score"]],
                    left_on=decode_key,
                    right_on="threshold",
                    how="left"
                )

                # Combine clean + merged attacked rows
                merged_df = pd.concat([df_clean, merged_attacked], ignore_index=True)

            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            merged_df.to_csv(output_csv, index=False)
            print(f"✅ Saved merged: {output_csv}")





if __name__ == "__main__":
    attacks = [
        "decrease_brightness",
        "increase_brightness",
        "crop",
        "jpeg",
        "mask",
        "noise",
        "overlay",
        "resize",
        "rotate"
    ]

    # Methods and image names remain constant
    methods = ["dwtDct", "dwtDctSvd"]
    image_names = [
        "cat", "city_day", "city_night", "desert", "dog", "fish", "food",
        "forest", "man1", "man2", "man3", "mountain", "pages", "woman1", "woman2"
    ]

    # Run the merge for each attack
    for attack in attacks:
        print(f"\n🌀 Processing attack type: {attack}")
        merge_lpips_and_decode(
            lpips_base_dir="lpips_scores_original",
            decode_base_dir="threshold_tests/original",
            output_base_dir="decode_lpips_results_original",
            attack=attack,
            methods=methods,
            image_names=image_names
        )


