#!/usr/bin/env python3
"""
Test script to verify all dependencies are installed correctly
"""

import sys

def test_imports():
    """Test that all required packages can be imported"""
    packages = [
        ('streamlit', 'Streamlit'),
        ('aiohttp', 'aiohttp'),
        ('bs4', 'BeautifulSoup4'),
        ('lxml', 'lxml'),
        ('pandas', 'Pandas'),
        ('plotly', 'Plotly'),
        ('validators', 'Validators'),
        ('urllib3', 'urllib3'),
        ('textstat', 'textstat'),
        ('aiofiles', 'aiofiles'),
    ]
    
    print("Testing package imports...\n")
    
    all_good = True
    for module_name, display_name in packages:
        try:
            __import__(module_name)
            print(f"✅ {display_name} - OK")
        except ImportError as e:
            print(f"❌ {display_name} - FAILED: {e}")
            all_good = False
    
    print("\n" + "="*50)
    if all_good:
        print("✅ All packages imported successfully!")
        print("\nYou can now run the app with:")
        print("  streamlit run app.py")
    else:
        print("❌ Some packages failed to import.")
        print("\nPlease install missing packages with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    test_imports()
