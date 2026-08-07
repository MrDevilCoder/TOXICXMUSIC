#!/usr/bin/env python3
"""
Automated package maintenance script
"""

import subprocess
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

class PackageManager:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self):
        """Create backup of current packages"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"requirements-{timestamp}.txt"
        
        with open("requirements.txt", "r") as src, open(backup_file, "w") as dst:
            dst.write(src.read())
        
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    
    def check_outdated(self):
        """Check for outdated packages"""
        print("🔍 Checking for outdated packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "list", "--outdated"])
    
    def update_critical(self):
        """Update only critical packages"""
        critical = [
            "pyrogram", "tgcrypto", "aiohttp", "flask",
            "fastapi", "uvicorn", "yt-dlp", "redis",
            "cloudflare", "Pillow", "sqlalchemy"
        ]
        
        for package in critical:
            print(f"📦 Updating {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--upgrade", package
            ])
    
    def update_all(self):
        """Update all packages"""
        print("📦 Updating all packages...")
        
        # Read requirements
        with open("requirements.txt", "r") as f:
            packages = [line.split("==")[0] for line in f if "==" in line]
        
        for package in packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "--upgrade", package
                ])
                print(f"  ✅ {package}")
            except:
                print(f"  ❌ {package}")
    
    def freeze_requirements(self):
        """Generate new requirements.txt"""
        print("📝 Generating new requirements.txt...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "freeze", ">", "requirements.txt"
        ])
        print("✅ requirements.txt updated!")

def main():
    manager = PackageManager()
    
    print("=" * 50)
    print("🔧 Telegram Music Bot - Package Manager")
    print("=" * 50)
    print("1. Check outdated packages")
    print("2. Update critical packages only")
    print("3. Update all packages")
    print("4. Full update with backup")
    print("5. Exit")
    
    choice = input("\nEnter choice (1-5): ")
    
    if choice == "1":
        manager.check_outdated()
    elif choice == "2":
        manager.create_backup()
        manager.update_critical()
        manager.freeze_requirements()
    elif choice == "3":
        manager.create_backup()
        manager.update_all()
        manager.freeze_requirements()
    elif choice == "4":
        manager.create_backup()
        manager.update_critical()
        manager.update_all()
        manager.freeze_requirements()
        print("\n✅ Full update complete!")
    else:
        print("Exiting...")

if __name__ == "__main__":
    main()
