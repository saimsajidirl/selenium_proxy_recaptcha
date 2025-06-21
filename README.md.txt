# Concurrent Selenium Sessions with Proxy and 2Captcha Integration

This Python script launches multiple concurrent Selenium sessions using authenticated proxies, and automatically solves Google's reCAPTCHA challenges using the 2Captcha API.

## 🚀 Features

- Proxy authentication using a temporary Chrome extension
- reCAPTCHA checkbox and challenge solving using 2Captcha
- IP verification from multiple services
- Concurrent execution via multithreading
- Headless evasion via various Chrome flags

## 📦 Requirements

- Python 3.6+
- Google Chrome
- ChromeDriver (must match your Chrome version and be in system PATH)

## 🔧 Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/selenium-proxy-2captcha.git
    cd selenium-proxy-2captcha
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Download ChromeDriver** (if not already):
    - [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads)

4. **Edit the script**:
    - Replace the 2Captcha API key with your own.
    - Update proxy credentials in `proxy_configs` list.

## ▶️ Usage

Run the script with:

```bash
python main.py
