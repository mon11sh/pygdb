#!/usr/bin/env python3
"""
GDB Python Fullstack - Master Dependency Setup Helper
Automates dependency installation for all 8 microservices and React frontend.
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("🏦 GDB Python Fullstack - Master Setup Helper")
    print("=" * 60)
    
    base_dir = Path(__file__).parent.resolve()
    
    services = [
        "accounts_service",
        "transactions_service",
        "users_service",
        "auth_service",
        "aadhar_service",
        "company_crv_service",
        "notification_service",
        "central_payment_gateway_service"
    ]
    
    # 1. Install requirements for all Python backend services
    success_count = 0
    for service in services:
        req_file = base_dir / service / "requirements.txt"
        if req_file.exists():
            print(f"\n📦 [{service}] Installing requirements...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
                print(f"✅ [{service}] Requirements installed successfully")
                success_count += 1
            except Exception as e:
                print(f"❌ [{service}] Failed to install requirements: {e}")
        else:
            print(f"⚠️  [{service}] No requirements.txt found")
            
    # 2. Install npm dependencies for React frontend
    frontend_dir = base_dir / "frontend"
    frontend_success = False
    if (frontend_dir / "package.json").exists():
        print(f"\n📦 [frontend] Installing npm dependencies (npm install)...")
        try:
            # Use shell=True for Windows compatibility to resolve global npm command
            subprocess.check_call("npm install", shell=True, cwd=str(frontend_dir))
            print("✅ [frontend] npm dependencies installed successfully")
            frontend_success = True
        except Exception as e:
            print(f"❌ [frontend] Failed to install npm dependencies: {e}")
            print("💡 Alternative: Please run 'npm install' manually inside the 'frontend' folder.")
            
    print("\n" + "=" * 60)
    print("📊 Setup Summary:")
    print(f"   ✓ Backend Services Configured: {success_count}/{len(services)}")
    print(f"   ✓ Frontend Configured: {'YES' if frontend_success else 'NO'}")
    print("=" * 60)
    print("🎉 All dependencies setup is complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
