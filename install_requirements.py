import subprocess

with open("requirements.txt") as f:
    for package in f:
        package = package.strip()
        if package:  # Ignore empty lines
            try:
                subprocess.check_call(["pip", "install", package])
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}, continuing...")
