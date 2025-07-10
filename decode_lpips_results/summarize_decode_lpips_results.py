import os
import pandas as pd
import numpy as np

# Adjust if needed
BASE_DIR = "decode_lpips_results"
METHODS = ["dwtDct", "dwtDctSvd", "rivaGan"]

summary_data = []

# Find all attack folders
attack_dirs = [d for d in os.listdir(BASE_DIR) if d.endswith("_test_results")]

for attack_dir in attack_dirs:
    attack_name = attack_dir.replace("_test_results", "")
    for method in METHODS:
        method_dir = os.path.join(BASE_DIR, attack_dir, "512x512", method)
        if not os.path.exists(method_dir):
            continue

        thresholds = []
        lpips_scores = []
        total_images = 0
        clean_decodable_images = 0

        for file in os.listdir(method_dir):
            if not file.endswith("_merged_results.csv"):
                continue

            file_path = os.path.join(method_dir, file)
            df = pd.read_csv(file_path)

            total_images += 1

            # Check if clean image can be decoded
            clean_row = df[df["attack_type"] == "clean"]
            if clean_row.empty or not clean_row["can_decode_clean"].iloc[0]:
                continue  # Skip this image
            clean_decodable_images += 1

            # Use first row with a valid first_failure value
            first_failure_row = df[df['first_failure'].notna()].head(1)
            if not first_failure_row.empty:
                threshold = first_failure_row['threshold'].values[0]
                lpips = first_failure_row['lpips_score'].values[0]
                if pd.notna(threshold) and pd.notna(lpips):
                    thresholds.append(float(threshold))
                    lpips_scores.append(float(lpips))
                    # debug check
                    # print(file_path, "  threshold:", threshold, "lpips:", lpips)

        # Add stats if any valid clean-decodable images
        if thresholds and lpips_scores:
            summary_data.append({
                "Attack": attack_name,
                "Method": method,
                "Avg Threshold": round(np.mean(thresholds), 3),
                "Std Threshold": round(np.std(thresholds), 3),
                "Avg LPIPS": round(np.mean(lpips_scores), 3),
                "Std LPIPS": round(np.std(lpips_scores), 3)
            })
        elif clean_decodable_images == 0:
            # All images failed to decode clean → method not applicable
            summary_data.append({
                "Attack": attack_name,
                "Method": method,
                "Avg Threshold": "--",
                "Std Threshold": "--",
                "Avg LPIPS": "--",
                "Std LPIPS": "--"
            })

# Convert to DataFrame and save
summary_df = pd.DataFrame(summary_data)
summary_df = summary_df.sort_values(by=["Attack", "Method"])
summary_df.to_csv("decode_lpips_summary.csv", index=False)
print("✅ Summary saved to decode_lpips_summary.csv")

# ----- LaTeX Table Generation -----

# Map method names for display
method_map = {
    "dwtDct": "DWT-DCT",
    "dwtDctSvd": "DWT-DCT-SVD",
    "rivaGan": "RivaGAN"
}
summary_df["Method"] = summary_df["Method"].map(method_map)

latex_lines = [
    "\\begin{table}[ht]",
    "\\centering",
    "\\caption{Average Thresholds and LPIPS Scores (± std) at First Decode Failure}",
    "\\label{tab:avg_threshold_lpips}",
    "\\renewcommand{\\arraystretch}{1.2}",
    "\\begin{tabular}{|l|c|c|c|}",
    "\\hline",
    "\\textbf{Attack Type} & \\textbf{DWT-DCT} & \\textbf{DWT-DCT-SVD} & \\textbf{RivaGAN} \\\\",
    "\\hline"
]

# Build two rows per attack
for attack in summary_df["Attack"].unique():
    row_thresh = [attack]
    row_lpips = [""]
    for method in ["DWT-DCT", "DWT-DCT-SVD", "RivaGAN"]:
        subdf = summary_df[(summary_df["Attack"] == attack) & (summary_df["Method"] == method)]
        if not subdf.empty:
            r = subdf.iloc[0]
            if r["Avg Threshold"] == "--":
                row_thresh.append("--")
                row_lpips.append("--")
            else:
                row_thresh.append(f"Threshold: {r['Avg Threshold']} $\\pm$ {r['Std Threshold']}")
                row_lpips.append(f"LPIPS: {r['Avg LPIPS']} $\\pm$ {r['Std LPIPS']}")
        else:
            row_thresh.append("--")
            row_lpips.append("--")

    latex_lines.append(" & ".join(row_thresh) + " \\\\")
    latex_lines.append(" & ".join(row_lpips) + " \\\\")
    latex_lines.append("\\hline")

latex_lines.extend([
    "\\end{tabular}",
    "\\end{table}"
])

with open("decode_lpips_latex_table.tex", "w") as f:
    f.write("\n".join(latex_lines))

print("✅ LaTeX table written to decode_lpips_latex_table.tex")
