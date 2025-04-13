import asyncio
from playwright.async_api import async_playwright, expect


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await context.tracing.start(
            screenshots=True, snapshots=True, sources=True
        )
        page = await context.new_page()
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.goto("https://www.coursera.org/?authMode=login")
        # print(await page.title())
        # Actions, first it will click on the login button, then it will fill the email and password fields, and finally it will click on the login button
        await page.click("text=Log In")
        await page.fill("input[name@email.com']","23BTRCN075@jainuniversity.ac.in")
        await page.fill("input[name='password']","#123@Evi")
        await page.click("button[type='submit']")
        await page.screenshot(path="screenshots/courseraLogin.png")
        # Assertions, it will check if the login was successful by checking if the profile button is visible
        await expect(page.locator("text=Profile")).to_be_visible()
        await expect(page.locator("text=Profile")).to_have_text("Profile")
        # stop tracing
        await context.tracing.stop(path="tracing/courseraLogin.zip")
        # close browser
        # add a sleep of 5 to see the result
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())