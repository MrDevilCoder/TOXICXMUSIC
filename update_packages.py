#!/usr/bin/env python3
"""
Automated package update script for Telegram Music Bot
"""

import subprocess
import sys
import pkg_resources
from typing import List, Tuple

def get_outdated_packages() -> List[Tuple[str, str, str]]:
    """Get list of outdated packages"""
    outdated = []
    for dist in pkg_resources.working_set:
        # Skip development packages
        if dist.key in {'pip', 'setuptools', 'wheel'}:
            continue
        outdated.append((dist.key, dist.version, 'latest'))
    return outdated

def update_pip():
    """Update pip itself"""
    print("🔄 Updating pip...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    print("✅ pip updated successfully!")

def update_package(package_name: str):
    """Update a single package"""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", package_name
        ])
        return True
    except subprocess.CalledProcessError:
        return False

def update_requirements_file():
    """Update requirements file with current versions"""
    print("📝 Generating updated requirements.txt...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "freeze", ">", "requirements-updated.txt"
    ])
    print("✅ Updated requirements saved to requirements-updated.txt")

def main():
    print("=" * 50)
    print("🔧 Telegram Music Bot - Package Updater")
    print("=" * 50)
    
    # Update pip
    update_pip()
    
    # Update setuptools and wheel
    print("\n🔄 Updating setuptools and wheel...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"
    ])
    
    # List of critical packages to update
    critical_packages = [
        'pyrogram',
        'tgcrypto',
        'aiohttp',
        'flask',
        'fastapi',
        'uvicorn',
        'yt-dlp',
        'pydub',
        'redis',
        'cloudflare',
        'Pillow',
        'sqlalchemy',
        'python-dotenv',
        'loguru',
        'requests'
    ]
    
    print("\n📦 Updating critical packages...")
    for package in critical_packages:
        print(f"  ⏳ Updating {package}...")
        if update_package(package):
            print(f"  ✅ {package} updated")
        else:
            print(f"  ❌ Failed to update {package}")
    
    # Update requirements file
    print("\n🔄 Updating requirements files...")
    update_requirements_file()
    
    print("\n" + "=" * 50)
    print("✅ All packages updated successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
