import asyncio
from playwright.async_api import async_playwright, expect, Page, BrowserContext, Browser
import os
import json # Import json for handling state file existence/read errors

# --- Configuration ---
EMAIL = "23BTRCN075@jainuniversity.ac.in"
PASSWORD = "#123@Evi" # Consider using environment variables for credentials
SCREENSHOT_DIR = "screenshots"
TRACING_DIR = "tracing"
AUTH_FILE_PATH = "coursera_auth_state.json" # Path to save/load state

# --- Helper Functions ---

async def close_overlays(page: Page):
    """Attempts to close common overlays like cookie banners."""
    try:
        print("Checking for overlays...")
        # Combine selectors into a single string
        accept_selector = (
            'button:has-text("Accept"), ' # Note the comma and space
            'button:has-text("Accept all cookies"), '
            'button:has-text("Agree"), '
            '[aria-label*="accept i"], '
            '[aria-label*="agree i"], '
            '[data-testid*="accept"], '
            '[id*="accept"]'
        )
        accept_button = page.locator(accept_selector).first
        await accept_button.click(timeout=5000)
        print("Closed an overlay/banner.")
    except Exception as e:
        # It's okay if not found, just log it.
        print(f"Overlay/banner not found or could not be closed (this is often ok): {e}")

async def perform_login(page: Page):
    """Fills login credentials and submits the form."""
    print("Performing login...")
    await page.goto("https://www.coursera.org/?authMode=login")
    await close_overlays(page) # Attempt to close overlays right after navigation
    await page.fill("input[name='email']", EMAIL)
    await page.fill("input[name='password']", PASSWORD)
    await page.click("button[type='submit']")
    try:
        # Wait for potential redirects or initial load after submit
        await page.wait_for_load_state("domcontentloaded", timeout=15000) # Increased timeout
    except Exception as e:
        print(f"Initial page load waiting error after submit (can be ignored): {e}")

async def handle_manual_intervention(page: Page):
    """Pauses the script to allow manual completion of CAPTCHAs."""
    print("\n\n============================================================")
    print("WAITING FOR MANUAL INTERVENTION:")
    print("If you see a security puzzle, CAPTCHA or verification challenge,")
    print("please solve it now in the browser window.")
    print("============================================================\n")
    input("Press Enter in this terminal after you've completed any security challenges (or if none appeared)...")
    print("Continuing with automation...")
    # Ensure screenshot directory exists before saving
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "courseraAfterManualIntervention.png"))

async def verify_login(page: Page, is_checking_state: bool = False) -> bool: # Add is_checking_state parameter
    """Checks if the login appears successful."""
    print("Verifying login status...")

    # Take a screenshot for visual confirmation
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    screenshot_path = os.path.join(SCREENSHOT_DIR, "verify_login_state_check.png" if is_checking_state else "verify_login_page.png")
    await page.screenshot(path=screenshot_path)
    print(f"Current page URL: {page.url}")

    try:
        # Combine selectors into a single string
        logged_in_selector = (
            'button[data-e2e="header-user-menu"], ' 
            '[aria-label*="Account"], '
            '[aria-label*="profile"], '
            'img[alt*="Profile"], '
            'img[alt*="profile"], '
            '.c-ph-avatar, '
            '.user-avatar, '
            'a[href*="/user/profile"]'
        )
        logged_in_locator = page.locator(logged_in_selector).first

        # Try to find login elements but don't fail if not found
        # Use a shorter timeout when just checking state
        timeout = 5000 if is_checking_state else 10000
        is_visible = await logged_in_locator.is_visible(timeout=timeout)
        if is_visible:
            print("Login appears successful - found user profile elements.")
            return True
    except Exception as e:
        print(f"Warning: Error checking login elements: {e}")

    # Check URL as secondary verification
    current_url = page.url
    print(f"Checking URL: {current_url}")

    # More flexible URL check - after login, URL likely has changed from login page
    # Also check if we are on the target learning page already
    if ("/learn" in current_url or 
        "/home" in current_url or 
        "/browse" in current_url or
        (not is_checking_state and "authMode=login" not in current_url)): # If checking state, being off login page isn't enough
         print("URL check: Seems to be logged in or on a relevant page.")
         return True
         
    print("URL check: Does not confirm login.")
    
    # If checking loaded state, don't ask user, just return failure
    if is_checking_state:
        print("Loaded state appears invalid or expired.")
        return False

    # Since we had manual intervention, let's trust the user also logged in manually if needed
    user_confirmation = input("Could not automatically verify login. Are you logged in? (y/n): ").lower().strip()
    if user_confirmation == 'y' or user_confirmation == 'yes':
        print("Login confirmed by user.")
        return True
        
    print("Login not confirmed.")
    return False

async def navigate_to_learning_page(page: Page):
    """Navigates to the 'My Learning' or equivalent page if not already there."""
    print("\nChecking if already on a learning page...")
    current_url = page.url
    if "/learn" in current_url or "/home" in current_url:
        print("Already on a learning/dashboard page.")
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "learningPage_already_there.png"))
        return # No need to navigate

    print("Navigating to My Learning page...")
    await asyncio.sleep(3) # Extra wait for elements to settle after login/intervention

    # Prioritize more specific selectors first
    dashboard_selectors = [
        'a[data-e2e="dashboard-link"]', # Specific data attribute
        'a:has-text("My Learning")',
        'a:has-text("My Courses")',
        'a:has-text("Dashboard")',
        'a[href*="/learn"]', # More general link patterns
        'a[href*="/home"]'
    ]

    navigated = False
    for selector in dashboard_selectors:
        try:
            print(f"Trying navigation selector: {selector}")
            target_link = page.locator(selector).first
            # Check if visible before clicking
            if await target_link.is_visible(timeout=5000):
                await target_link.click()
                print(f"Clicked element matching: {selector}")
                # Wait for navigation to likely complete
                await page.wait_for_load_state("domcontentloaded", timeout=20000) # Longer timeout
                await asyncio.sleep(3) # Wait after load for JS rendering
                # Verify URL changed to expected pattern
                if "/learn" in page.url or "/home" in page.url:
                    navigated = True
                    print("Navigation successful (URL check).")
                    break # Exit loop once navigation is successful
                else:
                    print(f"Clicked {selector}, but URL is now {page.url}. Trying next selector.")
            else:
                 print(f"Selector {selector} not visible.")
        except Exception as e:
            print(f"Selector {selector} failed: {e}")

    if not navigated:
        print("Could not find/use standard navigation links. Trying direct navigation to /learn...")
        try:
            await page.goto("https://www.coursera.org/learn", timeout=25000) # Longer timeout for direct nav
            await page.wait_for_load_state("domcontentloaded", timeout=20000)
            if "/learn" in page.url or "/home" in page.url:
                 navigated = True
                 print("Direct navigation to /learn successful.")
            else:
                 print("Direct navigation attempted, but ended at wrong URL.")
        except Exception as e:
            print(f"Direct navigation to /learn failed: {e}")
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "navigationFailed.png"))
            raise ConnectionError("Failed to navigate to the learning page.")

    if navigated:
        print("Successfully on a learning/dashboard page.")
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "learningPage.png"))
    else:
        print("ERROR: Failed to reach learning page after all attempts.")
        raise ConnectionError("Failed to navigate to the learning page.")


async def get_enrolled_courses(page: Page) -> list[dict]:
    """Scrapes the list of enrolled courses from the current page."""
    print("\nScraping enrolled courses...")
    courses = []
    # Refined selectors based on common Coursera structures (needs verification)
    # Look for course cards, items within a list, or sections with course titles
    course_selectors = [
        'div[data-e2e="course-card"]', # Primary target
        'li[class*="course-list-item"]',
        'div[class*="rc-CourseCard"]',
        'div[class*="course-card-container"]',
        'a[data-track-component="my_courses_card"]' # Another potential card link
    ]

    course_elements = []
    for selector in course_selectors:
        print(f"Trying course container selector: {selector}")
        elements = await page.locator(selector).all()
        if elements:
            print(f"Found {len(elements)} elements with selector: {selector}")
            course_elements = elements
            break # Use the first selector that finds elements
        else:
            print(f"Selector {selector} found no elements.")

    if not course_elements:
        print("Warning: Could not find course elements using primary selectors.")
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "noCourseElementsFound.png"))
        return [] # Return empty list if no containers found

    print(f"Processing {len(course_elements)} potential course elements...")

    for i, element in enumerate(course_elements):
        title = None
        link = None
        try:
            # Extract title - try multiple common patterns within the card
            title_locators = [
                element.locator('h2'),
                element.locator('h3'),
                element.locator('[data-e2e="course-card-title"]'),
                element.locator('span[class*="course-name"]'),
                element.locator('div[class*="card-title"]')
            ]
            for title_locator in title_locators:
                 if await title_locator.count() > 0:
                      title_text = await title_locator.first.text_content()
                      if title_text:
                           title = title_text.strip()
                           break # Use first found title

            # Extract link - find the main link, often wrapping the card or title
            link_locators = [
                 element.locator('a[href*="/learn/"]').first, # Link directly on the element or inside
                 element.locator('xpath=./ancestor-or-self::a[@href]').first # Check if element or ancestor is a link
            ]
            for link_locator in link_locators:
                 if await link_locator.count() > 0:
                      href = await link_locator.get_attribute('href')
                      if href and "/learn/" in href: # Ensure it looks like a course link
                           link = href
                           break # Use first found valid link

            # Ensure absolute URL
            if link and not link.startswith(('http:', 'https:')):
                link = f"https://www.coursera.org{link}"

            if title and link:
                # Avoid duplicates if multiple selectors match same course
                if not any(c['url'] == link for c in courses):
                    courses.append({"title": title, "url": link})
                    print(f"  - Found: {title} ({link})")
                else:
                    print(f"  - Duplicate found, skipped: {title}")
            else:
                 print(f"  - Skipped element {i+1}: Missing title ('{title}') or link ('{link}').")
                 os.makedirs(SCREENSHOT_DIR, exist_ok=True)
                 await element.screenshot(path=os.path.join(SCREENSHOT_DIR, f"skipped_course_element_{i+1}.png"))

        except Exception as e:
            print(f"Error processing course element {i+1}: {e}")
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            try:
                # Try screenshotting the problematic element
                await element.screenshot(path=os.path.join(SCREENSHOT_DIR, f"error_course_element_{i+1}.png"))
            except Exception as ss_error:
                 print(f"Could not take screenshot of error element: {ss_error}")


    if not courses:
         print("Could not extract any valid courses after processing elements.")
         os.makedirs(SCREENSHOT_DIR, exist_ok=True)
         await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "noCoursesExtracted.png"))

    return courses


# --- Main Setup Function ---
async def setup_coursera_session(headless=False, enable_tracing=True) -> tuple[Browser | None, BrowserContext | None, Page | None, object | None]:
    """Launches browser, loads state if available, otherwise logs in,
       and navigates to learning page. Saves state on successful fresh login."""
    playwright = None
    browser = None
    context = None
    page = None
    loaded_state_successfully = False

    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)

        # --- Try loading saved state ---
        if os.path.exists(AUTH_FILE_PATH):
            print(f"Attempting to load authentication state from {AUTH_FILE_PATH}...")
            try:
                context = await browser.new_context(
                    storage_state=AUTH_FILE_PATH,
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()
                print("Navigating to learning page to check loaded state...")
                # Go directly to the target page
                await page.goto("https://www.coursera.org/learn", timeout=25000, wait_until="domcontentloaded")
                await asyncio.sleep(3) # Allow time for redirects/rendering

                # Verify if the loaded state is still valid
                if await verify_login(page, is_checking_state=True):
                    print("Successfully loaded and verified existing session.")
                    loaded_state_successfully = True
                    # Optional: Start tracing now if needed for the loaded session
                    if enable_tracing:
                         os.makedirs(TRACING_DIR, exist_ok=True)
                         await context.tracing.start(screenshots=True, snapshots=True, sources=True)
                else:
                    print("Loaded state is invalid or expired. Proceeding with full login.")
                    await page.close()
                    await context.close() # Close the context with invalid state
                    context = None # Reset context
                    page = None    # Reset page

            except Exception as e:
                print(f"Error loading state or verifying login: {e}. Proceeding with full login.")
                if page: await page.close()
                if context: await context.close()
                context, page = None, None # Reset

        # --- Perform full login if state didn't load or was invalid ---
        if not loaded_state_successfully:
            print("Performing full login...")
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            if enable_tracing:
                os.makedirs(TRACING_DIR, exist_ok=True)
                await context.tracing.start(screenshots=True, snapshots=True, sources=True)

            page = await context.new_page()

            await perform_login(page)
            await handle_manual_intervention(page) # Keep manual step for initial login

            if not await verify_login(page): # Use standard verification here
                 raise Exception("Login verification failed after manual intervention.")

            # Ensure we are on the learning page before saving state
            await navigate_to_learning_page(page)

            # --- Save authentication state ---
            print(f"Login successful. Saving authentication state to {AUTH_FILE_PATH}...")
            await context.storage_state(path=AUTH_FILE_PATH)
            print("Authentication state saved.")

        # At this point, we should have a valid context and page
        if not page or not context:
             raise Exception("Failed to establish a valid session.")

        return browser, context, page, playwright # Return all necessary objects

    except Exception as e:
         print(f"Error during session setup: {e}")
         # Clean up resources if setup fails partially
         if page: await page.close()
         if context:
             if enable_tracing and await context.tracing.is_enabled():
                 try:
                     await context.tracing.stop(path=os.path.join(TRACING_DIR, "setup_error_trace.zip"))
                 except Exception: pass # Ignore tracing stop errors during cleanup
             await context.close()
         if browser: await browser.close()
         if playwright and playwright._impl_obj._was_started: await playwright.stop()
         # Return None for all values to indicate failure
         return None, None, None, None


# --- Example Usage (for testing this module directly) ---
async def run_test():
    browser, context, page, playwright = None, None, None, None # Initialize
    try:
        browser, context, page, playwright = await setup_coursera_session(headless=False)

        if not page: # Check if setup failed
             print("Session setup failed. Exiting test.")
             return

        courses = await get_enrolled_courses(page)
        print("\n--- Enrolled Courses ---")
        if courses:
            for course in courses:
                print(f"- {course['title']} ({course['url']})")
        else:
            print("No courses were extracted.")

        # Example: Navigate to the first course found
        if courses:
             print(f"\nNavigating to first course: {courses[0]['title']}")
             await page.goto(courses[0]['url'])
             await page.wait_for_load_state("domcontentloaded")
             await asyncio.sleep(5)
             os.makedirs(SCREENSHOT_DIR, exist_ok=True)
             await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "first_course_page.png"))
             print("Screenshot of the first course page saved.")

    except Exception as e:
        print(f"\nAn error occurred during test run: {e}")
        if page: # Try to screenshot on error
             os.makedirs(SCREENSHOT_DIR, exist_ok=True)
             await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "test_run_error.png"))
    finally:
        print("Cleaning up test run...")
        if context and await context.pages(): # Check if context still has pages
             if await context.tracing.is_enabled():
                 await context.tracing.stop(path=os.path.join(TRACING_DIR, "coursera_test_trace.zip"))
        if browser:
            await browser.close()
        # Ensure playwright stops if it was started
        if playwright and playwright._impl_obj._was_started:
             await playwright.stop()


# This ensures the test run only happens when executing this file directly
if __name__ == "__main__":
    # Make sure directories exist
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(TRACING_DIR, exist_ok=True)

    asyncio.run(run_test())