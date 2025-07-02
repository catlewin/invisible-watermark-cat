import os
import subprocess

attack_root = "threshold_tests/512x512_all_methods_results"
output_root = "lpips_scores"
methods = ["dwtDct", "dwtDctSvd", "rivaGan"]

for attack_folder in os.listdir(attack_root):
    attack_path = os.path.join(attack_root, attack_folder)
    if not os.path.isdir(attack_path):
        continue

    for method in methods:
        method_path = os.path.join(attack_path, method)
        if not os.path.isdir(method_path):
            continue

        for image_folder in os.listdir(method_path):
            image_path = os.path.join(method_path, image_folder)
            if not os.path.isdir(image_path):
                continue

            output_csv = os.path.join(
                output_root,
                attack_folder,
                "512x512",
                method,
                f"{image_folder}_lpips_scores.csv"
            )
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)

            print(f"🔎 Processing: {image_path}")
            cmd = [
                "python",
                "calculate_lpips_scores.py",
                "--dir", image_path,
                "--output_csv", output_csv
            ]
            subprocess.run(cmd, check=True)
