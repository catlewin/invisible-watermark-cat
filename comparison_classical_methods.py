import os
import pandas as pd
import numpy as np

attacks = [
    "decrease_brightness", "increase_brightness", "crop", "jpeg", "mask",
    "noise", "overlay", "resize", "rotate"
]
methods = ["dwtDct", "dwtDctSvd"]
images = [
    "cat", "city_day", "city_night", "desert", "dog", "fish", "food",
    "forest", "man1", "man2", "man3", "mountain", "pages", "woman1", "woman2"
]

resized_dir = "decode_lpips_results"
original_dir = "decode_lpips_results_original"

summary = []

def parse_clean_decode_stats(folder):
    clean_count = 0
    thresholds = []
    lpips_scores = []

    for fname in os.listdir(folder):
        if not fname.endswith("_merged_results.csv"):
            continue

        df = pd.read_csv(os.path.join(folder, fname))
        clean = df[df["attack_type"] == "clean"]

        if not clean.empty and clean["can_decode_clean"].iloc[0] == True:
            clean_count += 1
            failure = df[df["first_failure"].notna()].head(1)
            if not failure.empty:
                thresholds.append(failure["first_failure"].values[0])
                lpips = failure["lpips_score"].values[0] if "lpips_score" in failure.columns else None
                if pd.notna(lpips):
                    lpips_scores.append(lpips)

    return clean_count, thresholds, lpips_scores


def parse_clean_decode_count(folder):
    count = 0
    thresholds = []
    for fname in os.listdir(folder):
        if not fname.endswith("_merged_results.csv"):
            continue
        df = pd.read_csv(os.path.join(folder, fname))
        clean = df[df["attack_type"] == "clean"]
        if not clean.empty and clean["can_decode_clean"].iloc[0] == True:
            count += 1
            failure = df[df["first_failure"].notna()].head(1)
            if not failure.empty:
                thresholds.append(failure["first_failure"].values[0])
    return count, thresholds

for attack in attacks:
    for method in methods:
        resized_path = os.path.join(resized_dir, f"{attack}_test_results", "512x512", method)
        original_path = os.path.join(original_dir, f"{attack}_test_results", "original", method)
        if not os.path.isdir(resized_path) or not os.path.isdir(original_path):
            continue

        r_clean, r_thresh, r_lpips = parse_clean_decode_stats(resized_path)
        o_clean, o_thresh, o_lpips = parse_clean_decode_stats(original_path)

        r_avg_thresh = round(np.mean(r_thresh), 3) if r_thresh else "--"
        o_avg_thresh = round(np.mean(o_thresh), 3) if o_thresh else "--"

        r_avg_lpips = round(np.mean(r_lpips), 3) if r_lpips else "--"
        o_avg_lpips = round(np.mean(o_lpips), 3) if o_lpips else "--"

        summary.append({
            "Attack": attack,
            "Method": method,
            "Clean Decode": f"{r_clean} → {o_clean}",
            "Threshold": f"{r_avg_thresh} → {o_avg_thresh}",
            "LPIPS at Failure": f"{r_avg_lpips} → {o_avg_lpips}"
        })

# Save to markdown
df = pd.DataFrame(summary)
df = df.sort_values(by=["Attack", "Method"])

md_path = "original_vs_resized_comparison.md"

with open(md_path, "w") as f:
    f.write("| Attack | Method | Clean Decode ↑ | Threshold ↑ | LPIPS at Failure ↓ |\n")
    f.write("|--------|--------|----------------|--------------|---------------------|\n")
    for _, row in df.iterrows():
        f.write(f"| {row['Attack']} | {row['Method']} | {row['Clean Decode']} | {row['Threshold']} | {row['LPIPS at Failure']} |\n")

print("✅ Comparison written to original_vs_resized_comparison.md")
