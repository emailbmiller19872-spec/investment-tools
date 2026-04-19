#!/usr/bin/env python3
"""
CAPTCHA Solver Setup Guide
===========================

This script helps set up the free CAPTCHA solving system.
No paid APIs required!
"""

import os
import sys
import platform

def check_system():
    print("Checking system requirements for FREE CAPTCHA Solver...")
    print(f"OS: {platform.system()}")
    
    # Check Python version
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor} - OK")
    else:
        print(f"✗ Python {version.major}.{version.minor} - Needs Python 3.8+")
        return False
    
    return True

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    print("\nChecking Tesseract OCR installation...")
    
    if platform.system() == "Windows":
        try:
            import subprocess
            result = subprocess.run(['tesseract', '--version'], capture_output=True)
            if result.returncode == 0:
                print("✓ Tesseract found")
                return True
        except:
            pass
        
        print("✗ Tesseract not found")
        print("\nTo install Tesseract on Windows:")
        print("1. Download: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Run the installer")
        print("3. During installation, choose: C:\\Program Files\\Tesseract-OCR")
        print("4. Restart your terminal")
        return False
    
    elif platform.system() == "Linux":
        os.system("apt-get install tesseract-ocr")
        return True
    
    elif platform.system() == "Darwin":  # macOS
        os.system("brew install tesseract")
        return True
    
    return False

def setup_free_solver():
    """Configure the free CAPTCHA solver"""
    print("\n" + "="*60)
    print("FREE CAPTCHA SOLVER SETUP")
    print("="*60)
    
    if not check_system():
        print("\nSystem requirements not met. Please install Python 3.8+")
        return False
    
    print("\n[STEP 1] Installing Python dependencies...")
    os.system("pip install -r requirements.txt")
    
    print("\n[STEP 2] Tesseract OCR (for high accuracy image solving)...")
    has_tesseract = check_tesseract()
    
    if has_tesseract:
        print("✓ Tesseract configured - Image CAPTCHAs will be solved with high accuracy")
    else:
        print("⚠ Tesseract not installed - System will use fallback online OCR")
        print("  Install Tesseract for better CAPTCHA solving accuracy")
    
    print("\n[STEP 3] Email Notifications (optional)...")
    print("The bot can send email alerts when manual CAPTCHA solving is needed")
    
    use_email = input("\nEnable email notifications? (y/n): ").lower() == 'y'
    
    if use_email:
        print("\nFor Gmail:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate an app password")
        print("3. Copy it to EMAIL_PASSWORD in .env")
        
        email = input("Enter your Gmail address: ")
        notification_email = input("Enter notification email (can be same as Gmail): ")
        
        # Update .env
        with open('.env', 'r') as f:
            env_content = f.read()
        
        env_content = env_content.replace(
            "EMAIL_ADDRESS=your_gmail@gmail.com",
            f"EMAIL_ADDRESS={email}"
        )
        env_content = env_content.replace(
            "NOTIFICATION_EMAIL=your_email@example.com",
            f"NOTIFICATION_EMAIL={notification_email}"
        )
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✓ Email configured in .env")
    
    print("\n" + "="*60)
    print("FREE CAPTCHA SOLVER FEATURES:")
    print("="*60)
    print("""
    ✓ OCR-based Solving: Uses Tesseract/Online OCR for image CAPTCHAs
    ✓ Browser Bypass: Attempts to bypass detection through browser manipulation
    ✓ Pattern Recognition: Learns from solved CAPTCHAs (caching)
    ✓ Manual Fallback: Notifies you when manual solving is needed
    ✓ Email Alerts: Optional email notifications
    ✓ 100% FREE: No subscription required
    
    Solving Methods (in order of attempt):
    1. Browser automation bypass (iframe manipulation)
    2. Headless browser detection bypass
    3. OCR image extraction and solving
    4. Online OCR service (free tier)
    5. Manual notification with screenshot
    """)
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("""
    1. Configure your wallet in .env:
       WALLET_ADDRESS=your_address
       PRIVATE_KEY=your_key
    
    2. (Optional) Set up proxies in .env:
       PROXIES=http://proxy1:port,http://proxy2:port
    
    3. Run the bot:
       python main.py
    """)
    
    return True

if __name__ == "__main__":
    success = setup_free_solver()
    sys.exit(0 if success else 1)
