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
        
        # After manual intervention, take a screenshot to see what we're looking at
        print("Taking screenshot of current page state...")
        await page.screenshot(path="screenshots/courseraAfterLogin.png")
        
        # Try to verify login success with more flexible approach
        try:
            # Look for any indicators that we're logged in - profile menu, user avatar, etc.
            logged_in = await page.locator('button[data-e2e="header-user-menu"], [aria-label*="Account"], img[alt*="Profile"], .c-ph-avatar, .user-avatar').is_visible(timeout=5000)
            if logged_in:
                print("Login appears successful - found user profile elements.")
            else:
                print("Warning: Could not confirm successful login. Continuing anyway...")
        except Exception as e:
            print(f"Error checking login status: {e}")
            print("Continuing anyway...")
        
        print("Giving page time to fully load...")
        await asyncio.sleep(5)  # Add a fixed delay instead of waiting for network idle
        
        # Taking a screenshot to help debug what we're seeing
        await page.screenshot(path="screenshots/beforeNavigation.png")
        
        # Print all links on the page to help debug navigation options
        print("\nAvailable navigation options:")
        try:
            nav_links = await page.locator('a').all()
            for i, link in enumerate(nav_links[:10]):  # Show first 10 links
                link_text = await link.text_content()
                if link_text and link_text.strip():
                    print(f"Link {i}: {link_text.strip()}")
        except Exception as e:
            print(f"Error listing links: {e}")

        # Try to find the dashboard/course link with more flexible selectors
        print("\nLooking for course navigation links...")
        try:
            dashboard_selectors = [
                'a:has-text("My Learning")', 
                'a:has-text("My Courses")',
                'a:has-text("Dashboard")',
                'a[href*="home"]',
                'a[href*="dashboard"]',
                'a[href*="learn"]',
                '[data-e2e="home-link"]',
                '[data-track-component="home_dropdown"]'
            ]
            
            for selector in dashboard_selectors:
                print(f"Trying selector: {selector}")
                if await page.locator(selector).count() > 0:
                    print(f"Found matching element with selector: {selector}")
                    await page.locator(selector).first.click()
                    print("Clicked on navigation element")
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(3)  # Wait a bit more for page to stabilize
                    await page.screenshot(path="screenshots/afterNavigation.png")
                    break
            else:
                print("Could not find a suitable navigation link to courses")
                # Try an alternative approach - maybe go directly to a common URL
                print("Trying direct navigation to dashboard...")
                await page.goto("https://www.coursera.org/learn")
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
        except Exception as e:
            print(f"Error during navigation: {e}")
            # Fallback to direct navigation
            print("Error occurred. Trying direct navigation to courses page...")
            await page.goto("https://www.coursera.org/learn")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)
        
        # Take final screenshot of whatever page we landed on
        print("Taking screenshot of final page...")
        await page.screenshot(path="screenshots/finalCoursePage.png")
        print("Final screenshot saved. Check the screenshots folder to see what happened.")

        # stop tracing
        await context.tracing.stop(path="tracing/courseraLogin.zip")
        # close browser
        # add a sleep of 5 to see the result
        await asyncio.sleep(1000)
        await browser.close()

asyncio.run(main())