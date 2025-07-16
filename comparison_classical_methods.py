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

def fmt_stats(values):
    if values:
        avg = round(np.mean(values), 3)
        std = round(np.std(values), 3)
        return f"{avg} ± {std}"
    else:
        return "--"

# Gather stats
for attack in attacks:
    for method in methods:
        resized_path = os.path.join(resized_dir, f"{attack}_test_results", "512x512", method)
        original_path = os.path.join(original_dir, f"{attack}_test_results", "original", method)
        if not os.path.isdir(resized_path) or not os.path.isdir(original_path):
            continue

        r_clean, r_thresh, r_lpips = parse_stats(resized_path)
        o_clean, o_thresh, o_lpips = parse_stats(original_path)

        summary.append({
            "Attack": attack,
            "Method": method,
            "Clean Decode (Resized → Original)": f"{r_clean} → {o_clean}",
            "Threshold (Resized → Original)": f"{fmt_stats(r_thresh)} → {fmt_stats(o_thresh)}",
            "LPIPS at Failure (Resized → Original)": f"{fmt_stats(r_lpips)} → {fmt_stats(o_lpips)}"
        })

# Create DataFrame
df = pd.DataFrame(summary)
df = df.sort_values(by=["Attack", "Method"])

# Save Markdown
md_path = "original_vs_resized_comparison_detailed.md"
with open(md_path, "w") as f:
    f.write("| Attack | Method | Clean Decode (Resized → Original) | Threshold (Resized → Original) | LPIPS at Failure (Resized → Original) |\n")
    f.write("|--------|--------|----------------|--------------|---------------------|\n")
    for _, row in df.iterrows():
        f.write(
            f"| {row['Attack']} | {row['Method']} | {row['Clean Decode (Resized → Original)']} | "
            f"{row['Threshold (Resized → Original)']} | {row['LPIPS at Failure (Resized → Original)']} |\n"
        )

# Save to LaTeX
latex_path = "original_vs_resized_comparison_detailed.tex"
with open("original_vs_resized_comparison_latex.tex", "w") as f:
    f.write("\\begin{table}[h!]\n\\centering\n")
    f.write("\\begin{tabular}{llccc}\n\\toprule\n")
    f.write("Attack & Method & Clean Decode & Threshold & LPIPS at Failure \\\\\n")
    f.write("\\midrule\n")
    for _, row in df.iterrows():
        attack = row["Attack"].replace("_", "\\_")  # escape LaTeX underscores
        f.write(
            f"{attack} & {row['Method']} & {row['Clean Decode (Resized → Original)']} & "
            f"{row['Threshold (Resized → Original)']} & {row['LPIPS at Failure (Resized → Original)']} \\\\\n"
        )
    f.write("\\bottomrule\n\\end{tabular}\n")
    f.write("\\caption{Comparison of clean decode counts, average thresholds, and LPIPS at first failure between resized and original images.}\n")
    f.write("\\label{tab:original_vs_resized}\n\\end{table}\n")

print("📄 LaTeX table saved as original_vs_resized_comparison_latex.tex")
