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

summary = []

def parse_stats(folder):
    thresholds = []
    lpips_scores = []

    for fname in os.listdir(folder):
        if not fname.endswith("_merged_results.csv"):
            continue

        df = pd.read_csv(os.path.join(folder, fname))
        clean = df[df["attack_type"] == "clean"]

        if not clean.empty and clean["can_decode_clean"].iloc[0] == True:
            failure = df[df["first_failure"].notna()].head(1)
            if not failure.empty:
                thresholds.append(failure["first_failure"].values[0])
                lpips = failure["lpips_score"].values[0] if "lpips_score" in failure.columns else None
                if pd.notna(lpips):
                    lpips_scores.append(lpips)

    return thresholds, lpips_scores

def delta_stats(orig_values, resized_values):
    if orig_values and resized_values:
        delta_avg = round(np.mean(orig_values) - np.mean(resized_values), 3)
        delta_std = round(np.std(orig_values) - np.std(resized_values), 3)
        return f"{delta_avg} ± {delta_std}"
    else:
        return "--"

# Gather stats
for attack in attacks:
    for method in methods:
        resized_path = os.path.join(resized_dir, f"{attack}_test_results", "512x512", method)
        original_path = os.path.join(original_dir, f"{attack}_test_results", "original", method)
        if not os.path.isdir(resized_path) or not os.path.isdir(original_path):
            continue

        r_thresh, r_lpips = parse_stats(resized_path)
        o_thresh, o_lpips = parse_stats(original_path)

        summary.append({
            "Attack": attack,
            "Method": method,
            "Threshold Δ": delta_stats(o_thresh, r_thresh),
            "LPIPS at Failure Δ": delta_stats(o_lpips, r_lpips)
        })

# Create DataFrame
df = pd.DataFrame(summary)
df = df.sort_values(by=["Attack", "Method"])

# Save Markdown
md_path = "original_vs_resized_delta.md"
with open(md_path, "w") as f:
    f.write("| Attack | Method | Threshold Δ | LPIPS at Failure Δ |\n")
    f.write("|--------|--------|--------------|---------------------|\n")
    for _, row in df.iterrows():
        f.write(
            f"| {row['Attack']} | {row['Method']} | {row['Threshold Δ']} | {row['LPIPS at Failure Δ']} |\n"
        )

# Save to LaTeX
latex_path = "original_vs_resized_delta.tex"
with open(latex_path, "w") as f:
    f.write("\\begin{table}[h!]\n\\centering\n")
    f.write("\\begin{tabular}{llcc}\n\\toprule\n")
    f.write("Attack & Method & Threshold $\\Delta$ & LPIPS at Failure $\\Delta$ \\\\\n")
    f.write("\\midrule\n")
    for _, row in df.iterrows():
        attack = row["Attack"].replace("_", " ")  # escape LaTeX underscores
        f.write(
            f"{attack} & {row['Method']} & {row['Threshold Δ']} & {row['LPIPS at Failure Δ']} \\\\\n"
        )
    f.write("\\bottomrule\n\\end{tabular}\n")
    f.write("\\caption{Delta in average thresholds and LPIPS at first failure between original and resized images.}\n")
    f.write("\\label{tab:original_vs_resized_delta}\n\\end{table}\n")

print("✅ Markdown and LaTeX delta tables saved.")
