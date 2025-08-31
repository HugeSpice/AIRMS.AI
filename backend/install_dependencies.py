#!/usr/bin/env python3
"""
Installation script for AI Risk Mitigation System dependencies

This script helps install all required dependencies including:
- Enhanced PII Detection (Presidio, spaCy)
- Bias & Fairness Detection (Fairlearn, AIF360)
- Adversarial Detection (TextAttack, ART)
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_python_packages():
    """Install Python packages from requirements.txt"""
    print("📦 Installing Python packages...")
    
    # Upgrade pip first
    if not run_command("python -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def install_spacy_model():
    """Install spaCy English model"""
    print("🔤 Installing spaCy English model...")
    
    try:
        # Try to load the model first
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy English model already installed")
            return True
        except OSError:
            # Model not found, install it
            if run_command("python -m spacy download en_core_web_sm", "Installing spaCy English model"):
                return True
            else:
                return False
    except ImportError:
        print("❌ spaCy not installed. Please install requirements first.")
        return False

def verify_installations():
    """Verify that all key components are properly installed"""
    print("🔍 Verifying installations...")
    
    verification_results = []
    
    # Check Presidio
    try:
        from presidio_analyzer import AnalyzerEngine
        print("✅ Presidio Analyzer installed")
        verification_results.append(True)
    except ImportError:
        print("❌ Presidio Analyzer not installed")
        verification_results.append(False)
    
    # Check spaCy
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy with English model installed")
        verification_results.append(True)
    except ImportError:
        print("❌ spaCy not installed")
        verification_results.append(False)
    except OSError:
        print("❌ spaCy English model not installed")
        verification_results.append(False)
    
    # Check Fairlearn
    try:
        import fairlearn
        print("✅ Fairlearn installed")
        verification_results.append(True)
    except ImportError:
        print("❌ Fairlearn not installed")
        verification_results.append(False)
    
    # Check AIF360
    try:
        import aif360
        print("✅ AIF360 installed")
        verification_results.append(True)
    except ImportError:
        print("❌ AIF360 not installed")
        verification_results.append(False)
    
    # Check TextAttack
    try:
        import textattack
        print("✅ TextAttack installed")
        verification_results.append(True)
    except ImportError:
        print("❌ TextAttack not installed")
        verification_results.append(False)
    
    # Check ART
    try:
        import art
        print("✅ Adversarial Robustness Toolbox installed")
        verification_results.append(True)
    except ImportError:
        print("❌ Adversarial Robustness Toolbox not installed")
        verification_results.append(False)
    
    # Check other dependencies
    try:
        import numpy
        import pandas
        import sklearn
        import transformers
        import torch
        print("✅ Core ML libraries installed")
        verification_results.append(True)
    except ImportError as e:
        print(f"❌ Core ML libraries not installed: {e}")
        verification_results.append(False)
    
    return verification_results

def main():
    """Main installation process"""
    print("🚀 AI Risk Mitigation System - Dependency Installer")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    
    # Install Python packages
    if not install_python_packages():
        print("❌ Failed to install Python packages")
        sys.exit(1)
    
    # Install spaCy model
    if not install_spacy_model():
        print("❌ Failed to install spaCy model")
        sys.exit(1)
    
    # Verify installations
    verification_results = verify_installations()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Installation Summary")
    print("=" * 60)
    
    successful = sum(verification_results)
    total = len(verification_results)
    
    if successful == total:
        print("🎉 All components installed successfully!")
        print("✅ Your AI Risk Mitigation System is ready to use!")
    else:
        print(f"⚠️  {successful}/{total} components installed successfully")
        print("❌ Some components failed to install")
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Ensure you have sufficient disk space")
        print("3. Try running: pip install --upgrade setuptools wheel")
        print("4. For GPU support, install PyTorch with CUDA: https://pytorch.org/")
        print("5. Some packages may require system dependencies (e.g., gcc, build-essential)")
    
    print("\n🔧 Next steps:")
    print("1. Test the system: python -m pytest tests/")
    print("2. Run the API: python run.py")
    print("3. Check the dashboard: http://localhost:3000")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
