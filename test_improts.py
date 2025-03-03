

print("Überprüfe Standardbibliothek-Module...")
try:
    import os
    import time
    import re
    import io
    import sys
    import threading
    import base64
    import uuid
    from urllib.parse import urlparse, urljoin
    print("✅ Alle Standardbibliothek-Module gefunden")
except ImportError as e:
    print(f"❌ Fehler bei Standardbibliothek: {e}")

print("\nÜberprüfe externe Module...")
try:
    import requests
    print("✅ requests importiert")
except ImportError:
    print("❌ requests nicht gefunden")

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, scrolledtext, messagebox
    print("✅ tkinter und Untermodule importiert")
except ImportError as e:
    print(f"❌ tkinter Fehler: {e}")

try:
    from bs4 import BeautifulSoup
    print("✅ BeautifulSoup importiert")
except ImportError:
    print("❌ beautifulsoup4 nicht gefunden")

try:
    from PIL import Image, ImageTk
    print("✅ Pillow (PIL) importiert")
except ImportError:
    print("❌ Pillow nicht gefunden")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    print("✅ selenium und Untermodule importiert")
except ImportError as e:
    print(f"❌ selenium Fehler: {e}")

try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("✅ webdriver-manager importiert")
except ImportError:
    print("❌ webdriver-manager nicht gefunden")

try:
    import markdown
    print("✅ markdown importiert")
except ImportError:
    print("❌ markdown nicht gefunden")