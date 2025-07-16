import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Config
attacks = ["denoising", "upscale"]
methods = ["dwtDct", "dwtDctSvd", "rivaGan"]
merged_root = "decode_lpips_results"
output_dir = "LPIPS_Binary_Attack_Graphs"
os.makedirs(output_dir, exist_ok=True)

for attack in attacks:
    avg_scores = {}
    std_scores = {}

    print(f"\n📊 Processing attack: {attack}")
    for method in methods:
        method_dir = os.path.join(merged_root, f"{attack}_test_results", "512x512", method)
        if not os.path.isdir(method_dir):
            print(f"⚠️ Missing: {method_dir}")
            continue

        lpips_scores = []
        decode_successes = []
        image_names = []

        for fname in os.listdir(method_dir):
            if not fname.endswith("_merged_results.csv"):
                continue

            file_path = os.path.join(method_dir, fname)
            df = pd.read_csv(file_path)

            attacked_row = df[df["attack_type"] == attack]
            if not attacked_row.empty and "lpips_score" in attacked_row.columns:
                score = attacked_row["lpips_score"].values[0]
                decode_success = attacked_row["success"].values[0] if "success" in attacked_row.columns else False

                if pd.notna(score):
                    lpips_scores.append(score)
                    decode_successes.append(bool(decode_success))
                    image_names.append(fname.replace("_merged_results.csv", ""))

        if not lpips_scores:
            print(f"  ❌ No LPIPS scores found for {method} on {attack}")
            continue

        # Save stats for group bar plot
        avg_scores[method] = sum(lpips_scores) / len(lpips_scores)
        std_scores[method] = pd.Series(lpips_scores).std()

        # 📈 Per-image bar plot
        plt.figure(figsize=(10, 4))
        # Color bars by decode success
        colors = ["green" if s else "red" for s in decode_successes]

        legend_elements = [
            Patch(facecolor='green', label='Decode Success'),
            Patch(facecolor='red', label='Decode Failure')
        ]
        plt.legend(handles=legend_elements, loc='upper right')

        plt.bar(image_names, lpips_scores, color=colors)
        plt.title(f"{method} LPIPS Scores per Image – {attack.capitalize()}")
        plt.ylabel("LPIPS Score")
        plt.xticks(rotation=45, ha="right")
        plt.ylim(0, max(lpips_scores) * 1.1)  # Add 10% padding
        plt.tight_layout()
        per_image_path = os.path.join(output_dir, f"{attack}_{method}_lpips_per_image.png")
        plt.savefig(per_image_path)
        plt.close()
        print(f"  ✅ Saved per-image plot: {per_image_path}")

    # 📊 Group bar plot: Avg LPIPS per method
    if avg_scores:
        plt.figure(figsize=(6, 4))
        bars = list(avg_scores.values())
        errors = [std_scores[m] for m in avg_scores]
        labels = list(avg_scores.keys())

        plt.bar(labels, bars, yerr=errors, capsize=5)
        plt.title(f"Avg LPIPS Scores with Std Dev – {attack.capitalize()}")
        plt.ylabel("Avg LPIPS ± Std Dev")
        ymax = max(b + e for b, e in zip(bars, errors)) * 1.1  # max bar + std, plus 10% padding
        plt.ylim(0, ymax)
        plt.tight_layout()
        avg_path = os.path.join(output_dir, f"{attack}_avg_lpips_per_method.png")
        plt.savefig(avg_path)
        plt.close()
        print(f"✅ Saved average LPIPS plot: {avg_path}")
