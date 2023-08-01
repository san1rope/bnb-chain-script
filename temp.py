import time
import traceback
from typing import Optional

import user_agent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_markup(url: str, delay: Optional[float] = None) -> Optional[str]:
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-agent={user_agent.generate_user_agent()}")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless")

    service = Service(ChromeDriverManager(version="114.0.5735.90").install())

    driver = webdriver.Chrome(service=service, options=options)
    markup = None
    try:
        driver.get(url)
        if delay:
            time.sleep(delay)

        markup = driver.page_source
    except Exception:
        print(traceback.format_exc())
    finally:
        driver.close()
        driver.quit()

    return markup


def main():
    print(get_markup("https://swap.ws/#!/auth", delay=5))


if __name__ == "__main__":
    main()
