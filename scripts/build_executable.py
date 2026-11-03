"""Automated PyInstaller build script to package SlidePDF Studio into a standalone executable.

Usage:
    python scripts/build_executable.py [--onefile]
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def build():
    parser = argparse.ArgumentParser(description="Package SlidePDF Studio into a standalone binary/exe")
    parser.add_argument("--onefile", action="store_true", help="Create a single monolithic executable file")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print("=== SlidePDF Studio Build Automation ===")
    print(f"Target OS: {platform.system()} {platform.machine()}")

    # Find customtkinter location to bundle assets
    try:
        import customtkinter
        ctk_path = Path(customtkinter.__file__).parent
        print(f"Found CustomTkinter at: {ctk_path}")
    except ImportError:
        print("Error: customtkinter not installed in current python environment.")
        sys.exit(1)

    sep = ";" if platform.system() == "Windows" else ":"
    ctk_data_arg = f"{ctk_path}{sep}customtkinter"
    assets_data_arg = f"assets{sep}assets"

    icon_file = "assets/icon.png"
    if platform.system() == "Windows" and os.path.exists("assets/icon.ico"):
        icon_file = "assets/icon.ico"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=SlidePDF-Studio",
        "--windowed",  # No black terminal window
        "--clean",
        "--noconfirm",
        f"--add-data={ctk_data_arg}",
        f"--add-data={assets_data_arg}",
        f"--icon={icon_file}",
        "--paths=src",
        "src/slidepdf/app.py",
    ]

    if args.onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    print("\nRunning PyInstaller command:")
    print(" ".join(cmd))
    print("-" * 50)

    res = subprocess.run(cmd)
    if res.returncode == 0:
        dist_dir = project_root / "dist"
        print("\n" + "=" * 50)
        print("✓ BUILD SUCCESSFUL!")
        print(f"Standalone application generated in: {dist_dir}")
        if args.onefile:
            exe_name = "SlidePDF-Studio.exe" if platform.system() == "Windows" else "SlidePDF-Studio"
            print(f"Executable binary: {dist_dir / exe_name}")
        else:
            print(f"Application bundle folder: {dist_dir / 'SlidePDF-Studio'}")
        print("=" * 50)
    else:
        print(f"\n✕ Build failed with exit code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    build()
