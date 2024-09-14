import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

downloader_url = "https://ytmp3s.nu/Sj09/"
search_box_id = "url"
submit_btn_css = "input[type='submit']"
convert_next_btn_xpath = "/html/body/form/div[2]/a[2]"
downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")


def get_latest_file(download_dir):
    """Returns the latest file from the download directory."""
    files = os.listdir(download_dir)
    paths = [os.path.join(download_dir, filename) for filename in files]
    return max(paths, key=os.path.getctime) if paths else None


def get_download(driver, link):
    """
    Attempts to download the MP3 for the given link.
    Returns True if the download was successful, False otherwise.
    """
    try:
        search_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, search_box_id)))
        time.sleep(1)
        search_box.send_keys(link)

        convert_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_btn_css)))
        time.sleep(1)
        convert_button.click()

        # Wait for either the download button or the back button to be clickable
        button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//a[@rel="nofollow"]')))
        href = button.get_attribute('href')

        if href == 'https://ytmp3s.nu/':
            print(f'Download unsuccessful. Bad link: {link}')
            driver.save_screenshot('error_screenshot.png')
            time.sleep(2)
            button.click()
            return False
        else:
            before_download = get_latest_file(downloads_dir)
            button.click()

            # Switch to pop-up tab
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            main_tab = driver.current_window_handle
            new_tab = driver.window_handles[-1]
            driver.switch_to.window(new_tab)

            # Wait to see if a new file download starts
            for sec in range(10):
                time.sleep(1)
                after_download = get_latest_file(downloads_dir)
                if before_download != after_download:
                    driver.close()    # close the pop-up tab after download starts
                    driver.switch_to.window(main_tab)
                    time.sleep(2)
                    click_next_conversion_button(driver)
                    return True
            return False

    except Exception as e:
        exception = type(e).__name__
        print(f"{exception} error occurred")
        driver.save_screenshot('error_screenshot.png')
        return False


def click_next_conversion_button(driver):
    """Click the 'convert-next' button for a new search."""
    try:
        convert_next_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, convert_next_btn_xpath)))
        convert_next_btn.click()
    except Exception as e:
        exception = type(e).__name__
        print(f'Clicking "convert-next" button was unsuccessful')
        print(f'{exception} error occurred')
        driver.save_screenshot('error_screenshot.png')


def run_bot():
    """Reads YT links from txt file and downloads them from YT-mp3 website."""
    with open('links.txt', 'r') as file:
        links = [line.strip() for line in file.readlines()]

    print(links)

    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": downloads_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(downloader_url)

    successful_downloads = 0
    for link in links:
        if get_download(driver, link):
            successful_downloads += 1

    print(f"Successful downloads: {successful_downloads} / {len(links)}")


if __name__ == "__main__":
    run_bot()
