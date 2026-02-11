#!/usr/bin/env python3
"""
STIX Dashboard Setup Script
Handles the stix>=1.2.0.0 library conflict by providing multiple installation options
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def install_main_requirements():
    """Install main requirements without the conflicting stix library"""
    print("Installing main requirements (without legacy stix library)...")
    return run_command("pip install -r requirements_FIXED_v2.txt")

def install_legacy_stix():
    """Attempt to install legacy stix library"""
    print("Attempting to install legacy stix library...")
    print("WARNING: This may cause conflicts with other dependencies!")
    
    # Try different approaches
    approaches = [
        "pip install stix==1.2.0.0 --no-deps",  # Install without dependencies
        "pip install stix==1.2.0.0 --force-reinstall",  # Force reinstall
        "pip install stix==1.2.0.0"  # Standard install
    ]
    
    for approach in approaches:
        print(f"Trying: {approach}")
        if run_command(approach, check=False):
            print("Legacy stix library installed successfully!")
            return True
        print("Failed, trying next approach...")
    
    print("Could not install legacy stix library.")
    return False

def create_virtual_environment():
    """Create a separate virtual environment for legacy STIX support"""
    print("Creating separate virtual environment for legacy STIX support...")
    
    venv_path = Path("venv_stix1")
    if venv_path.exists():
        print("Virtual environment already exists.")
        return True
    
    if not run_command(f"python -m venv {venv_path}"):
        return False
    
    # Install requirements in the new environment
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
    else:  # Unix-like
        pip_path = venv_path / "bin" / "pip"
    
    print("Installing requirements in separate environment...")
    if not run_command(f"{pip_path} install -r requirements_FIXED_v2.txt"):
        return False
    
    print("Installing legacy stix library in separate environment...")
    if not run_command(f"{pip_path} install stix==1.2.0.0", check=False):
        print("Warning: Could not install legacy stix library in separate environment")
    
    print(f"Separate environment created at: {venv_path}")
    print("To use it:")
    if os.name == 'nt':
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")
    
    return True

def main():
    print("STIX Dashboard Setup")
    print("=" * 50)
    print()
    print("This script helps resolve the stix>=1.2.0.0 library conflict.")
    print()
    print("Options:")
    print("1. Install without legacy STIX 1.x support (recommended)")
    print("2. Try to install with legacy STIX 1.x support (may cause conflicts)")
    print("3. Create separate virtual environment for legacy support")
    print("4. Exit")
    print()
    
    while True:
        choice = input("Choose an option (1-4): ").strip()
        
        if choice == "1":
            print("\nOption 1: Installing without legacy STIX support...")
            if install_main_requirements():
                print("\n✅ Installation successful!")
                print("Your dashboard will work with STIX 2.x files and basic STIX 1.x parsing.")
                print("For full STIX 1.x support, use option 3 to create a separate environment.")
            else:
                print("\n❌ Installation failed!")
            break
            
        elif choice == "2":
            print("\nOption 2: Installing with legacy STIX support...")
            install_main_requirements()
            if install_legacy_stix():
                print("\n✅ Installation successful with legacy support!")
                print("Warning: Monitor for dependency conflicts.")
            else:
                print("\n⚠️ Main installation successful, but legacy STIX support failed.")
                print("Consider using option 3 for a separate environment.")
            break
            
        elif choice == "3":
            print("\nOption 3: Creating separate virtual environment...")
            if create_virtual_environment():
                print("\n✅ Separate environment created successfully!")
                print("Use this environment when you need full STIX 1.x support.")
            else:
                print("\n❌ Failed to create separate environment!")
            break
            
        elif choice == "4":
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()