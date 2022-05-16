
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def run_kiosk(path):
  options = Options()
  options.add_argument("--kiosk")
  driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
  driver.get(path)
  while True:
    pass