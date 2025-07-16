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

def parse_stats(folder):
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


for attack in attacks:
    for method in methods:
        resized_path = os.path.join(resized_dir, f"{attack}_test_results", "512x512", method)
        original_path = os.path.join(original_dir, f"{attack}_test_results", "original", method)
        if not os.path.isdir(resized_path) or not os.path.isdir(original_path):
            continue

        r_clean, r_thresh, r_lpips = parse_stats(resized_path)
        o_clean, o_thresh, o_lpips = parse_stats(original_path)

        # Format with average ± std, or fallback to "--"
        def fmt_stats(values):
            if values:
                avg = round(np.mean(values), 3)
                std = round(np.std(values), 3)
                return f"{avg} ± {std}"
            else:
                return "--"

        summary.append({
            "Attack": attack,
            "Method": method,
            "Clean Decode ↑": f"{r_clean} → {o_clean}",
            "Threshold ↑": f"{fmt_stats(r_thresh)} → {fmt_stats(o_thresh)}",
            "LPIPS at Failure ↓": f"{fmt_stats(r_lpips)} → {fmt_stats(o_lpips)}"
        })

# Save to markdown
df = pd.DataFrame(summary)
df = df.sort_values(by=["Attack", "Method"])

md_path = "original_vs_resized_comparison_detailed.md"

with open(md_path, "w") as f:
    f.write("| Attack | Method | Clean Decode (Resized → Original) | Threshold (Resized → Original) | LPIPS at Failure (Resized → Original) |\n")
    f.write("|--------|--------|----------------|--------------|---------------------|\n")
    for _, row in df.iterrows():
        f.write(f"| {row['Attack']} | {row['Method']} | {row['Clean Decode ↑']} | {row['Threshold ↑']} | {row['LPIPS at Failure ↓']} |\n")

print("✅ Detailed comparison written to original_vs_resized_comparison_detailed.md")
