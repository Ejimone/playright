import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.coursera.org/")
        print(await page.title())
        await page.screenshot(path="coursera.png")
        await browser.close()

asyncio.run(main())
