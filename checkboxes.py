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
        await page.goto("https://demoqa.com/checkbox")
        # print(await page.title())
        # Actions
        await page.check('label[for="tree-node-home"]')
        await page.screenshot(path="screenshots/checkbox.png")
        # Assertions
        assert await page.is_checked('label[for="tree-node-home"]') is True
        await expect(page.locator("#result")).to_have_text("You selected :homedesktopnotescommandsdocumentsworks")
        # stop tracing
        await context.tracing.stop(path="tracing/checkbox.zip")
        # close browser
        await browser.close()


asyncio.run(main())
