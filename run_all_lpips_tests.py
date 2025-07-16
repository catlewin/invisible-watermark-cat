import os
import subprocess

attack_root = "threshold_tests/512x512"
output_root = "lpips_scores"
methods = ["dwtDct", "dwtDctSvd", "rivaGan"]

for attack_folder in ["denoising_test_results"]:
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

            # ⬇️ Handle special case for upscale
            if attack_folder == "upscale_test_results":
                # Create a temporary directory with just the needed files
                from tempfile import TemporaryDirectory
                import shutil

                with TemporaryDirectory() as tmpdir:
                    src_img = os.path.join(image_path, "rescaled_final.jpg")
                    ref_img = os.path.join(image_path, "original_watermarked.jpg")
                    if not (os.path.exists(src_img) and os.path.exists(ref_img)):
                        print(f"⚠️ Skipping {image_path} — required files missing")
                        continue
                    shutil.copy(src_img, os.path.join(tmpdir, "rescaled_final.jpg"))
                    shutil.copy(ref_img, os.path.join(tmpdir, "original_watermarked.jpg"))

                    cmd = [
                        "python",
                        "calculate_lpips_scores.py",
                        "--dir", tmpdir,
                        "--output_csv", output_csv
                    ]
                    subprocess.run(cmd, check=True)
            else:
                cmd = [
                    "python",
                    "calculate_lpips_scores.py",
                    "--dir", image_path,
                    "--output_csv", output_csv
                ]
                subprocess.run(cmd, check=True)
