# 🚀 Concurrent Selenium reCAPTCHA Solver with Proxy and 2Captcha Integration

> Automate browser sessions using authenticated proxies and bypass Google's reCAPTCHA using 2Captcha with concurrent execution.

---

## 📌 Overview

This project automates solving Google reCAPTCHA (checkbox and challenge) using Selenium and [2Captcha](https://2captcha.com), through proxies with authentication. Sessions run in parallel using threading to simulate real-world automation environments.

---

## 🧩 Features

- 🔐 Authenticated proxy support (`IP:PORT:USER:PASS`)
- 🤖 Automatic solving of reCAPTCHA v2 (checkbox/challenge)
- 💻 Chrome Extension generation for proxy auth
- 🌐 Public IP verification per proxy
- ⚙️ Headless-like browser automation
- 🧵 Multi-threaded execution
- 🧼 Auto cleanup of temporary extension files

---

## 🏗️ Requirements

- Python 3.7+
- Google Chrome
- ChromeDriver (compatible version) in your system `PATH`
- 2Captcha API Key
- Valid proxy credentials

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/selenium-recaptcha-proxy.git
cd selenium-recaptcha-proxy
pip install -r requirements.txt
```

### ⚙️ Configuration
#### 🔑 Add Proxies & 2Captcha Key

In `main.py`, edit these values:

```python
proxy_configs = [
    "IP:PORT:USERNAME:PASSWORD",
    "IP:PORT:USERNAME:PASSWORD"
]
```

Update your 2Captcha key:

```python
self.captcha_api_key = "YOUR_2CAPTCHA_API_KEY"
```

### 🚀 Running the Script

```bash
python main.py
```

Output will show:
- Proxy IP verification
- reCAPTCHA interaction
- 2Captcha solving status
- Final success/failure per session

---

## 📂 Folder Structure

```
.
├── main.py
├── requirements.txt
├── README.md
```

---

## 📄 Sample Log

```
Session Session-1: Starting session...
Session Session-1: Checking IP with https://api.myip.com/...
Session Session-1: Current IP: 185.186.62.127
Session Session-1: Navigating to reCAPTCHA demo...
Session Session-1: ✅ reCAPTCHA verification confirmed!
Session Session-1: ✅ Session completed successfully!
```

---

## ⚠️ Tips & Considerations

- Use residential or high-quality proxies to reduce blocks
- Monitor 2Captcha balance to avoid failures
- Don't abuse Google’s endpoints to avoid bans
- Adjust sleep/poll timing to mimic human behavior

---

## 📑 License

This project is open-source under the MIT License.

---

## 🤝 Acknowledgements

- Selenium
- 2Captcha
- MyIP.com

---

## 📧 Contact

Created by Muhammad Saim Sajid – feel free to reach out or contribute.
