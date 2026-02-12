#!/usr/bin/env python
"""
Build script for NeverLiie Package Manager.

Usage:
    python build.py              # Full build + installer
    python build.py --clean      # Clean old artifacts first
    python build.py --skip-build # Only rebuild installer
    python build.py --no-installer # Only Nuitka build, no installer
"""
import argparse
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VERSION_FILE = PROJECT_ROOT / "VERSION"
BUILD_DIR = PROJECT_ROOT / "main.build"
DIST_DIR = PROJECT_ROOT / "main.dist"


def get_version():
    if not VERSION_FILE.exists():
        raise FileNotFoundError("VERSION file not found")
    return VERSION_FILE.read_text().strip()


def clean_artifacts():
    dirs_to_remove = [BUILD_DIR, DIST_DIR]
    for d in dirs_to_remove:
        if d.exists():
            print(f"Removing {d}...")
            shutil.rmtree(d)
    print("Clean complete.\n")


def run_nuitka(version: str):
    print(f"Building nlpm v{version} with Nuitka...")
    
    cmd = [
        "py", "-m", "nuitka", "--standalone",
        "--company-name=Liiesl",
        "--product-name=NeverLiie Package Manager",
        "--file-description=NeverLiie Package Manager",
        f"--file-version={version}",
        f"--product-version={version}",
        "main.py"
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    if result.returncode != 0:
        raise RuntimeError("Nuitka build failed")
    
    shutil.copy2(VERSION_FILE, DIST_DIR / "VERSION")
    print(f"Copied VERSION file to {DIST_DIR}")
    print("Nuitka build complete.\n")


def run_nsis(version: str):
    print("Creating installer with NSIS...")
    
    installer_name = f"nlpm_setup_v{version}.exe"
    
    cmd = ["makensis", "make-installer.nsi"]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    if result.returncode != 0:
        raise RuntimeError("NSIS installer creation failed")
    
    installer_path = PROJECT_ROOT / installer_name
    print(f"\nInstaller created: {installer_path}")
    return installer_path


def main():
    parser = argparse.ArgumentParser(description="Build NLPM")
    parser.add_argument("--clean", action="store_true", help="Remove old build artifacts first")
    parser.add_argument("--skip-build", action="store_true", help="Skip Nuitka, only rebuild installer")
    parser.add_argument("--no-installer", action="store_true", help="Skip installer creation")
    args = parser.parse_args()
    
    version = get_version()
    print(f"Version: {version}\n")
    
    if args.clean:
        clean_artifacts()
    
    if not args.skip_build:
        run_nuitka(version)
    
    if not args.no_installer:
        run_nsis(version)
    
    print("\nBuild complete!")


if __name__ == "__main__":
    main()
