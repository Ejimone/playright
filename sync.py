from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Set headless=True to run in the background
    page = browser.new_page()
    page.goto("https://www.coursera.org/")
    # to screenshot the page
    page.screenshot(path="coursera.png")
    # to get the title of the page
    title = page.title()
    browser.close()


