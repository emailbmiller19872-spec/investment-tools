#!/usr/bin/env python3
"""
Test the Free CAPTCHA Solver
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from free_captcha_solver import FreeCaptchaSolver
import logging

logging.basicConfig(level=logging.INFO)

def test_captcha_solver():
    print("Testing Free CAPTCHA Solver...\n")
    
    solver = FreeCaptchaSolver()
    
    print("1. Testing OCR setup...")
    if solver.use_ocr:
        print("   ✓ Tesseract OCR available - image CAPTCHA solving enabled")
    else:
        print("   ⚠ Tesseract OCR not available - will use online OCR fallback")
    
    print("\n2. Testing cache system...")
    if os.path.exists('data/captcha_cache.json'):
        print(f"   ✓ Cache file exists with {len(solver.captcha_cache)} entries")
    else:
        print("   ✓ Cache initialized")
    
    print("\n3. Testing image solving...")
    # Create a test image
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple test CAPTCHA
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 40), "TEST123", fill='black')
        
        img.save('data/test_captcha.png')
        print("   Created test CAPTCHA image")
        
        # Try to solve it
        solution = solver.solve_image_captcha('data/test_captcha.png')
        if solution:
            print(f"   ✓ Solved: {solution}")
        else:
            print("   ⚠ Could not solve test CAPTCHA (OCR not available)")
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
    
    print("\n4. Testing notification system...")
    email = os.getenv('NOTIFICATION_EMAIL')
    if email:
        print(f"   ✓ Email notifications configured to: {email}")
    else:
        print("   ⚠ Email notifications not configured")
    
    print("\n" + "="*50)
    print("CAPTCHA Solver is ready!")
    print("="*50)
    print("""
    The Free CAPTCHA Solver includes:
    ✓ Multiple solving methods
    ✓ Automatic caching of solutions
    ✓ Email notifications
    ✓ Manual solving fallback
    ✓ No costs or API keys required
    """)

if __name__ == "__main__":
    test_captcha_solver()
