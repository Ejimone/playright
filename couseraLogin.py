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
        
        # Wait for initial page load, but with a shorter timeout
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception as e:
            print(f"Page load waiting error (can be ignored): {e}")
        
        print("\n\n============================================================")
        print("WAITING FOR MANUAL INTERVENTION:")
        print("If you see a security puzzle, CAPTCHA or verification challenge,")
        print("please solve it now in the browser window.")
        print("============================================================\n")
        
        # Wait for user to confirm they've solved any puzzles
        user_input = input("Press Enter after you've completed any security challenges (or if none appeared)...")
        print("Continuing with automation...")
        
        # Take screenshot after manual intervention
        await page.screenshot(path="screenshots/courseraLogin.png")
        
        # Try to verify login success with more flexible approach
        try:
            await expect(page.locator("text=Profile")).to_be_visible(timeout=10000)
            print("Login successful - profile element found.")
        except Exception:
            print("Profile element not found, but continuing anyway...")
        
        print("Giving page time to fully load...")
        await asyncio.sleep(5)  # Add a fixed delay instead of waiting for network idle

        # Navigate to My Courses/Learning page
        print("Navigating to My Learning...")
        # Using a selector that targets common text for user's courses/learning dashboard
        my_learning_link = page.locator('a:has-text("My learning"), a:has-text("My Courses"), [aria-label*="My learning i"], [data-e2e="dashboard-link"]')
        await my_learning_link.first.click()
        await page.wait_for_load_state("networkidle") # Wait for navigation to complete

        # Verify navigation to the courses page
        print("Verifying courses page...")
        # Check for a common heading or element indicating the courses list
        await expect(page.locator('h1:has-text("My Learning"), h2:has-text("My Courses"), [data-e2e="my-courses-heading"]')).to_be_visible(timeout=10000)
        print("Successfully navigated to My Learning page.")

        # Take a screenshot of the courses page
        await page.screenshot(path="screenshots/courseraMyCourses.png")
        print("Screenshot of My Courses page saved.")

        # stop tracing
        await context.tracing.stop(path="tracing/courseraLogin.zip")
        # close browser
        # add a sleep of 5 to see the result
        await asyncio.sleep(1000)
        await browser.close()

asyncio.run(main())