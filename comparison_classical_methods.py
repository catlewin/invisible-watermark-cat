import os
import pandas as pd
import numpy as np

attacks = [
    "decrease_brightness", "increase_brightness", "crop", "jpeg", "mask",
    "noise", "overlay", "resize", "rotate"
]
methods = ["dwtDct", "dwtDctSvd"]

resized_dir = "decode_lpips_results"
original_dir = "decode_lpips_results_original"

resized_ranges = {
    "crop": (0.4, 1.0),
    "decrease_brightness": (0.0, 1.0),
    "increase_brightness": (1.0, 3.0),
    "jpeg": (10, 100),
    "mask": (0, 100),
    "noise": (0, 50),
    "overlay": (0.0, 1.0),
    "resize": (0.10, 1.00),
    "rotate": (0, 20)
}

original_ranges = {
    "crop": (0.4, 1.0),
    "decrease_brightness": (0.2, 1.0),
    "increase_brightness": (1.0, 2.0),
    "jpeg": (50, 100),
    "mask": (0, 80),
    "noise": (0, 35),
    "overlay": (0.0, 0.50),
    "resize": (0.10, 1.00),
    "rotate": (0, 4)
}

inverted_attacks = {"crop", "jpeg", "decrease_brightness", "resize"}


def normalize(values, attack, is_resized):
    min_val, max_val = (resized_ranges if is_resized else original_ranges)[attack]
    values = np.array(values)
    normalized = (values - min_val) / (max_val - min_val)
    normalized = np.clip(normalized, 0, 1)
    if attack in inverted_attacks:
        normalized = 1.0 - normalized
    return normalized


def parse_stats(folder, attack, is_resized):
    thresholds = []
    lpips_scores = []
    for fname in os.listdir(folder):
        if not fname.endswith("_merged_results.csv"):
            continue
        df = pd.read_csv(os.path.join(folder, fname))
        if "first_failure" in df.columns:
            failure = df[df["first_failure"].notna()].head(1)
            if not failure.empty:
                threshold = failure["first_failure"].values[0]
                lpips = failure["lpips_score"].values[0] if "lpips_score" in failure.columns else None
                if pd.notna(threshold):
                    thresholds.append(threshold)
                if pd.notna(lpips):
                    lpips_scores.append(lpips)

    norm_thresh = normalize(thresholds, attack, is_resized) if thresholds else []
    return norm_thresh, lpips_scores


def fmt_delta(val_resized, val_original):
    if len(val_resized) == 0 or len(val_original) == 0:
        return "--"
    avg_resized = np.mean(val_resized)
    avg_original = np.mean(val_original)
    std_resized = np.std(val_resized)
    std_original = np.std(val_original)
    delta_avg = round(avg_original - avg_resized, 3)
    delta_std = round(std_original - std_resized, 3)
    return f"{delta_avg} ± {delta_std}"



summary = []

for attack in attacks:
    for method in methods:
        resized_path = os.path.join(resized_dir, f"{attack}_test_results", "512x512", method)
        original_path = os.path.join(original_dir, f"{attack}_test_results", "original", method)
        if not os.path.isdir(resized_path) or not os.path.isdir(original_path):
            continue

        r_thresh, r_lpips = parse_stats(resized_path, attack, is_resized=True)
        o_thresh, o_lpips = parse_stats(original_path, attack, is_resized=False)

        summary.append({
            "Attack": attack,
            "Method": method,
            "Delta Threshold": fmt_delta(r_thresh, o_thresh),
            "Delta LPIPS": fmt_delta(r_lpips, o_lpips)
        })

# Create DataFrame
summary_df = pd.DataFrame(summary).sort_values(by=["Attack", "Method"])

# Markdown Output
with open("original_vs_resized_delta.md", "w") as f:
    f.write("| Attack | Method | Δ Threshold | Δ LPIPS at Failure |\n")
    f.write("|--------|--------|---------------|---------------------|\n")
    for _, row in summary_df.iterrows():
        f.write(f"| {row['Attack']} | {row['Method']} | {row['Delta Threshold']} | {row['Delta LPIPS']} |\n")

# LaTeX Output
with open("original_vs_resized_comparison_delta.tex", "w") as f:
    f.write("\\begin{table*}[t]\n\\centering\n")
    f.write("\\begin{tabular}{llcc}\n\\toprule\n")
    f.write(
        "\\textbf{Attack} & \\textbf{Method} & \\textbf{$\\Delta$ in Threshold} & \\textbf{$\\Delta$ in LPIPS at Failure} \\\n")
    f.write("\\midrule\n")
    for _, row in summary_df.iterrows():
        attack = row["Attack"].replace("_", "\\_")
        f.write(f"{attack} & {row['Method']} & {row['Delta Threshold']} & {row['Delta LPIPS']} \\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
    f.write(
        "\\caption{Change in average normalized thresholds and LPIPS at first failure between resized and original images.}\n")
    f.write("\\label{tab:original_vs_resized_delta}\n\\end{table*}\n")

print("✅ Delta comparison markdown and LaTeX files saved.")
