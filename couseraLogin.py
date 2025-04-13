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

        # Try to close potential cookie banner/overlay before interacting with the form
        try:
            # Using a selector that might match common cookie consent buttons, wait briefly
            print("Checking for overlays...")
            accept_button = page.locator('button:has-text("Accept"), button:has-text("Accept all cookies"), [aria-label*="accept i"]').first
            await accept_button.click(timeout=5000) # Short timeout
            print("Closed an overlay/banner.")
        except Exception as e:
            print(f"Overlay/banner not found or could not be closed: {e}")

        # Actions: fill the email and password fields, and click the submit button
        await page.fill("input[name='email']", "23BTRCN075@jainuniversity.ac.in")
        await page.fill("input[name='password']", "#123@Evi")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="screenshots/courseraLogin.png")
        # Assertions, it will check if the login was successful by checking if the profile button is visible
        await expect(page.locator("text=Profile")).to_be_visible(timeout=10000)
        await expect(page.locator("text=Profile")).to_have_text("Profile")
        # stop tracing
        await context.tracing.stop(path="tracing/courseraLogin.zip")
        # close browser
        # add a sleep of 5 to see the result
        await asyncio.sleep(1000)
        await browser.close()

asyncio.run(main())