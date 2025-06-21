import random
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import threading
import json
import os
import tempfile
import shutil
import re


class ProxySession:
    def __init__(self, proxy_config, session_id):
        self.proxy_config = proxy_config
        self.session_id = session_id
        self.driver = None
        self.captcha_api_key = "a01a8728ab00cae5b11bfe28ba0095a3"
        self.extension_dir = None

    def create_proxy_extension(self, proxy_host, proxy_port, proxy_username, proxy_password):
        """Create a Chrome extension for proxy authentication"""
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy_host, proxy_port, proxy_username, proxy_password)

        # Create temporary directory for extension
        extension_dir = tempfile.mkdtemp()

        with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
            f.write(manifest_json)

        with open(os.path.join(extension_dir, "background.js"), "w") as f:
            f.write(background_js)

        return extension_dir

    def setup_driver(self):
        """Configure Chrome driver with proxy settings"""
        chrome_options = Options()

        # Parse proxy configuration
        proxy_parts = self.proxy_config.split(':')
        if len(proxy_parts) != 4:
            raise ValueError(f"Invalid proxy format. Expected 'host:port:username:password', got: {self.proxy_config}")
        
        proxy_host = proxy_parts[0]
        proxy_port = proxy_parts[1]
        proxy_username = proxy_parts[2]
        proxy_password = proxy_parts[3]

        # Create proxy extension
        self.extension_dir = self.create_proxy_extension(proxy_host, proxy_port, proxy_username, proxy_password)

        # Configure Chrome options
        chrome_options.add_argument(f'--load-extension={self.extension_dir}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions-file-access-check')
        chrome_options.add_argument('--disable-extensions-http-throttling')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Wait for extension to load
            time.sleep(3)
            
            return self.driver
        except Exception as e:
            print(f"Session {self.session_id}: Error setting up driver: {str(e)}")
            if self.extension_dir and os.path.exists(self.extension_dir):
                try:
                    shutil.rmtree(self.extension_dir)
                except:
                    pass
            raise

    def verify_proxy_ip(self):
        """Verify proxy IP is working"""
        try:
            service_url = "https://api.myip.com/"
            print(f"Session {self.session_id}: Checking IP with {service_url}...")
            self.driver.get(service_url)

            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            page_content = self.driver.find_element(By.TAG_NAME, "body").text.strip()

            try:
                ip_data = json.loads(page_content)
                current_ip = ip_data.get("ip", "Unknown")
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract IP from text
                ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', page_content)
                current_ip = ip_match.group() if ip_match else "Unknown"

            if current_ip and current_ip != "Unknown":
                print(f"Session {self.session_id}: Current IP: {current_ip}")
                return current_ip
            else:
                print(f"Session {self.session_id}: Failed to extract IP")
                return None

        except Exception as e:
            print(f"Session {self.session_id}: Error verifying IP: {str(e)}")
            return None

    def solve_captcha_with_2captcha(self, site_key, page_url, is_invisible=False):
        """Solve reCAPTCHA using 2Captcha's userrecaptcha method"""
        try:
            print(f"Session {self.session_id}: Submitting reCAPTCHA to 2Captcha...")

            submit_url = "http://2captcha.com/in.php"
            submit_data = {
                "key": self.captcha_api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1
            }

            if is_invisible:
                submit_data["invisible"] = 1

            # Submit the captcha request
            response = requests.post(submit_url, data=submit_data, timeout=30)
            result = response.json()

            if result.get("status") != 1:
                raise Exception(f"2Captcha submission failed: {result.get('error_text', 'Unknown error')}")

            captcha_id = result.get("request")
            print(f"Session {self.session_id}: Captcha ID received: {captcha_id}")

            # Wait a little before polling
            initial_wait = random.uniform(4, 7)
            print(f"Session {self.session_id}: Waiting {initial_wait:.2f}s before polling for result...")
            time.sleep(initial_wait)

            # Poll for the solution
            get_url = "http://2captcha.com/res.php"
            max_attempts = 60
            for attempt in range(max_attempts):
                time.sleep(5)
                poll_data = {
                    "key": self.captcha_api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }

                try:
                    poll_response = requests.get(get_url, params=poll_data, timeout=30)
                    result = poll_response.json()

                    if result.get("status") == 1:
                        captcha_solution = result.get("request")
                        print(f"Session {self.session_id}: ✅ Captcha solved by 2Captcha!")
                        return captcha_solution
                    elif result.get("request") == "CAPCHA_NOT_READY":
                        print(f"Session {self.session_id}: Waiting... ({attempt + 1}/{max_attempts})")
                        continue
                    else:
                        raise Exception(f"2Captcha polling error: {result.get('error_text', 'Unknown error')}")
                except requests.RequestException as e:
                    print(f"Session {self.session_id}: Network error during polling: {str(e)}")
                    continue

            raise Exception("Captcha solving timed out after max attempts")

        except Exception as e:
            print(f"Session {self.session_id}: ❌ Error during 2Captcha solving: {str(e)}")
            return None

    def handle_recaptcha_demo(self):
        """Navigate to reCAPTCHA demo and solve it"""
        try:
            print(f"Session {self.session_id}: Navigating to reCAPTCHA demo...")
            self.driver.get("https://www.google.com/recaptcha/api2/demo")

            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(f"Session {self.session_id}: Page loaded, looking for reCAPTCHA...")

            # Wait for reCAPTCHA iframe to appear
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='recaptcha/api2/anchor']"))
            )

            # Get site key
            site_key = None
            try:
                site_key_element = self.driver.find_element(By.CSS_SELECTOR, "[data-sitekey]")
                site_key = site_key_element.get_attribute("data-sitekey")
                print(f"Session {self.session_id}: Found site key from data-sitekey: {site_key}")
            except:
                try:
                    iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha/api2/anchor']")
                    src = iframe.get_attribute("src")
                    site_key_match = re.search(r'k=([^&]+)', src)
                    site_key = site_key_match.group(1) if site_key_match else None
                    print(f"Session {self.session_id}: Found site key from iframe src: {site_key}")
                except Exception as e:
                    print(f"Session {self.session_id}: Could not find site key: {str(e)}")
                    return False

            if not site_key:
                raise Exception("Could not find reCAPTCHA site key")

            # Click the reCAPTCHA checkbox
            print(f"Session {self.session_id}: Switching to reCAPTCHA iframe...")
            iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha/api2/anchor']")
            self.driver.switch_to.frame(iframe)

            checkbox = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
            )
            print(f"Session {self.session_id}: Clicking reCAPTCHA checkbox...")
            checkbox.click()

            # Wait a moment for response
            time.sleep(3)
            self.driver.switch_to.default_content()

            # Check if challenge iframe appears
            needs_solving = False
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='recaptcha/api2/bframe']"))
                )
                print(f"Session {self.session_id}: Challenge iframe detected - need to solve with 2Captcha")
                needs_solving = True
            except TimeoutException:
                print(f"Session {self.session_id}: No challenge iframe - checkbox might have been sufficient")
                needs_solving = False

            if needs_solving:
                print(f"Session {self.session_id}: Solving reCAPTCHA challenge with 2Captcha...")
                captcha_solution = self.solve_captcha_with_2captcha(
                    site_key,
                    "https://www.google.com/recaptcha/api2/demo"
                )

                if not captcha_solution:
                    raise Exception("Failed to solve captcha with 2Captcha")

                print(f"Session {self.session_id}: Injecting captcha solution...")
                
                # Inject the solution
                inject_script = f"""
                    const token = "{captcha_solution}";
                    
                    // Set the token in all g-recaptcha-response textareas
                    document.querySelectorAll('textarea[name="g-recaptcha-response"]').forEach(el => {{
                        el.style.display = 'block';
                        el.value = token;
                        el.innerHTML = token;
                        
                        // Trigger events
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }});

                    // Look for callback function
                    const recaptchaCallback = document.querySelector('[data-callback]');
                    if (recaptchaCallback) {{
                        const cb = recaptchaCallback.getAttribute('data-callback');
                        if (cb && typeof window[cb] === 'function') {{
                            window[cb](token);
                        }}
                    }}
                    
                    // Also try to call global callback if it exists
                    if (typeof window.grecaptcha !== 'undefined' && window.grecaptcha.execute) {{
                        try {{
                            window.grecaptcha.execute();
                        }} catch(e) {{
                            console.log('Grecaptcha execute error:', e);
                        }}
                    }}
                    
                    return 'Token injected successfully';
                """
                
                result = self.driver.execute_script(inject_script)
                print(f"Session {self.session_id}: Script result: {result}")
                
                # Wait for the token to be processed
                time.sleep(3)

            # Try to submit the form
            try:
                submit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "recaptcha-demo-submit"))
                )
                print(f"Session {self.session_id}: Submitting form...")
                submit_button.click()

                # Wait for success or page change
                WebDriverWait(self.driver, 15).until(
                    lambda driver: ("Verification Success" in driver.page_source or
                                   "successfully" in driver.page_source.lower() or
                                   driver.current_url != "https://www.google.com/recaptcha/api2/demo")
                )

                print(f"Session {self.session_id}: ✅ Form submitted successfully!")
                print(f"Session {self.session_id}: Current URL: {self.driver.current_url}")

                # Check for success indicators
                page_source = self.driver.page_source.lower()
                if ("verification success" in page_source or 
                    "successfully" in page_source or 
                    self.driver.current_url != "https://www.google.com/recaptcha/api2/demo"):
                    print(f"Session {self.session_id}: ✅ reCAPTCHA verification confirmed!")
                    return True
                else:
                    print(f"Session {self.session_id}: Form submitted but verification status unclear")
                    return True

            except TimeoutException:
                print(f"Session {self.session_id}: Timeout waiting for form submission result")
                return False
            except Exception as e:
                print(f"Session {self.session_id}: Error submitting form: {str(e)}")
                return False

        except Exception as e:
            print(f"Session {self.session_id}: ❌ Error handling reCAPTCHA: {str(e)}")
            return False

    def run_session(self):
        """Run the complete session workflow"""
        try:
            print(f"Session {self.session_id}: Starting session...")

            # Setup driver
            self.setup_driver()
            print(f"Session {self.session_id}: Driver setup completed")

            # Verify proxy IP
            current_ip = self.verify_proxy_ip()
            if not current_ip:
                print(f"Session {self.session_id}: Failed to verify proxy IP")
                return False

            # Navigate to reCAPTCHA demo and solve it
            success = self.handle_recaptcha_demo()

            if success:
                print(f"Session {self.session_id}: ✅ Session completed successfully!")
                # Keep browser open for a moment to see results
                time.sleep(10)
            else:
                print(f"Session {self.session_id}: ❌ Session failed")

            return success

        except Exception as e:
            print(f"Session {self.session_id}: Fatal error: {str(e)}")
            return False
        finally:
            # Cleanup
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            # Cleanup extension directory
            if self.extension_dir and os.path.exists(self.extension_dir):
                try:
                    shutil.rmtree(self.extension_dir)
                except:
                    pass


def run_concurrent_sessions():
    """Run two concurrent Selenium sessions with different proxies"""

    # Proxy configurations (format: host:port:username:password)
    proxy_configs = [
        "89.47.118.110:12323:14a9151236ead:83c4457c02",
        "185.186.62.127:12323:14a9151236ead:83c4457c02"
    ]

    # Create session objects
    sessions = [
        ProxySession(proxy_configs[0], "Session-1"),
        ProxySession(proxy_configs[1], "Session-2")
    ]

    # Create threads for concurrent execution
    threads = []
    results = {}

    def run_session_thread(session):
        """Thread wrapper for session execution"""
        try:
            results[session.session_id] = session.run_session()
        except Exception as e:
            print(f"Thread error for {session.session_id}: {str(e)}")
            results[session.session_id] = False

    # Start threads
    print("🚀 Starting concurrent sessions...")
    for session in sessions:
        thread = threading.Thread(target=run_session_thread, args=(session,))
        thread.daemon = True  # Allow main program to exit even if threads are running
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=300)  # 5 minute timeout per thread

    # Print final results
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print("=" * 50)

    for session_id, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{session_id}: {status}")

    successful_sessions = sum(1 for success in results.values() if success)
    print(f"\nCompleted: {successful_sessions}/{len(sessions)} sessions successful")

    return successful_sessions, len(sessions)


if __name__ == "__main__":
    print("Concurrent Selenium Sessions with Proxy and 2Captcha Integration")
    print("=" * 60)

    # Check requirements
    required_packages = ["selenium", "requests"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install selenium requests")
        exit(1)

    print("✅ All required packages found")
    print("⚠️  Make sure ChromeDriver is installed and in PATH")
    print("⚠️  Make sure proxy credentials are valid")
    print("⚠️  Make sure 2Captcha API key has sufficient balance")
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    try:
        successful, total = run_concurrent_sessions()
        print(f"\n🎯 Final Summary: {successful}/{total} sessions completed successfully")
    except KeyboardInterrupt:
        print("\n⚠️  Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Program error: {str(e)}")
