import asyncio
import os
import google.generativeai as genai
from playwright.async_api import Page, Browser, BrowserContext
from dotenv import load_dotenv # Import the function

# Load environment variables from .env file
load_dotenv()

# Import functions from our refactored Coursera module
import couseraLogin

# --- Configuration ---
# Configure the Gemini API Key (Use environment variables in production)
# Example: os.environ['GEMINI_API_KEY'] = "YOUR_API_KEY"
try:
    # Make sure to set the GEMINI_API_KEY environment variable before running
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
except KeyError:
    print("ERROR: GEMINI_API_KEY environment variable not set.")
    print("Please set the GEMINI_API_KEY environment variable and try again.")
    exit(1) # Exit if key is not set

# Configure Gemini model
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}
safety_settings = [ # Adjust safety settings as needed
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]
model = genai.GenerativeModel(model_name="gemini-1.0-pro", # Or use "gemini-1.5-flash" or "gemini-1.5-pro" if available
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# --- AI Interaction Functions ---

async def choose_course_with_ai(courses: list[dict]) -> dict | None:
    """Uses Gemini to choose a course from the list."""
    if not courses:
        print("No courses provided to choose from.")
        return None

    prompt_parts = [
        "You are an AI assistant helping a user navigate their Coursera courses., and you are to perform actions on the course, such as playing videos, answering quizzes, etc.",
        "Here is a list of the user's enrolled courses:",
    ]
    for i, course in enumerate(courses):
        prompt_parts.append(f"{i + 1}. {course['title']}")
    prompt_parts.append("\nWhich course should we focus on? Please respond with the number only.")

    print("\nAsking AI to choose a course...")
    try:
        # Use generate_content_async for non-blocking call
        response = await model.generate_content_async(prompt_parts)
        choice_text = response.text.strip()
        choice_index = int(choice_text) - 1

        if 0 <= choice_index < len(courses):
            chosen_course = courses[choice_index]
            print(f"AI chose: {chosen_course['title']}")
            return chosen_course
        else:
            print(f"AI provided an invalid choice number: {choice_text}")
            return None
    except ValueError:
        print(f"AI response was not a valid number: {response.text}")
        return None
    except Exception as e:
        print(f"Error interacting with Gemini API: {e}")
        # Check for specific API errors if needed
        # print(response.prompt_feedback)
        return None

async def interact_with_course(page: Page, course_url: str):
    """Navigates to the course and performs basic interactions (placeholder)."""
    print(f"\nNavigating to course: {course_url}")
    try:
        await page.goto(course_url, timeout=25000)
        await page.wait_for_load_state("domcontentloaded", timeout=20000)
        await asyncio.sleep(5) # Wait for dynamic content to potentially load
        os.makedirs(couseraLogin.SCREENSHOT_DIR, exist_ok=True)
        await page.screenshot(path=os.path.join(couseraLogin.SCREENSHOT_DIR, "course_main_page.png"))
        print("Screenshot of course main page saved.")
    except Exception as e:
        print(f"Error navigating to or loading course page {course_url}: {e}")
        os.makedirs(couseraLogin.SCREENSHOT_DIR, exist_ok=True)
        await page.screenshot(path=os.path.join(couseraLogin.SCREENSHOT_DIR, "course_navigation_error.png"))
        return # Stop interaction if navigation fails

    # --- Placeholder for AI-driven actions within the course ---
    # This section requires significant development and knowledge of Coursera's structure.
    print("\n--- Course Interaction (Placeholders) ---")
    print("Analyzing course page structure...")

    # Example: Find and click the first video play button (very basic, needs refinement)
    try:
        # More specific selectors might be needed
        play_button_selectors = [
            'button[aria-label*="Play video"]',
            'button[class*="play-button"]'
            '.video-js .vjs-play-control',
            'button[data-track-component="play_button"]'
        ]
        play_button = page.locator(", ".join(play_button_selectors)).first

        if await play_button.is_visible(timeout=7000):
            print("Found a potential video play button. Clicking it...")
            await play_button.click()
            await asyncio.sleep(3) # Brief pause after click
            await page.screenshot(path=os.path.join(couseraLogin.SCREENSHOT_DIR, "video_playing.png"))
            print("Screenshot after attempting to play video saved.")
        else:
            print("Could not find a visible play button with common selectors.")
    except Exception as e:
        print(f"Error trying to click play button: {e}")

    # Example: Find the first quiz link (very basic, needs refinement)
    try:
        quiz_link_selectors = [
            'a[href*="quiz"]',
            'a:has-text("Quiz")',
            'button:has-text("Quiz")',
            'a[data-track-component="quiz_link"]'
        ]
        quiz_link = page.locator(", ".join(quiz_link_selectors)).first

        if await quiz_link.is_visible(timeout=7000):
            quiz_text = await quiz_link.text_content()
            print(f"Found a potential quiz link: {quiz_text.strip() if quiz_text else 'No Text'}")
            # Placeholder: Navigate and interact with quiz using AI
            # await quiz_link.click()
            # await page.wait_for_load_state("domcontentloaded")
            # await page.screenshot(path=os.path.join(couseraLogin.SCREENSHOT_DIR, "quiz_page.png"))
            # quiz_content = await page.content() # Or scrape specific elements
            # ai_answers = await get_quiz_answers_from_ai(quiz_content)
            # await fill_quiz(page, ai_answers)
            print("Placeholder: Would navigate to quiz and use AI to answer.")
        else:
            print("Could not find a visible quiz link with common selectors.")
    except Exception as e:
        print(f"Error trying to find quiz link: {e}")

    print("--- End Course Interaction Placeholders ---")

# --- Main Agent Logic ---
async def main_agent():
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    playwright = None # Initialize playwright instance variable

    try:
        # 1. Setup session using the refactored module
        print("Setting up Coursera session...")
        # Pass playwright instance back for proper cleanup
        browser, context, page, playwright = await couseraLogin.setup_coursera_session(headless=False) # Start headed for observation

        if not page: # Check if setup failed (returned None)
            print("Coursera session setup failed. Exiting agent.")
            return

        # 2. Get enrolled courses
        courses = await couseraLogin.get_enrolled_courses(page)
        if not courses:
            print("No courses found on the learning page. Exiting.")
            return

        print("\n--- Extracted Courses ---")
        for i, course in enumerate(courses):
            print(f"{i+1}. {course['title']}")

        # 3. Let AI choose a course (optional, uncomment to use)
        # chosen_course = await choose_course_with_ai(courses)

        # For testing, just pick the first course
        chosen_course = courses[0] if courses else None
        if chosen_course:
             print(f"\nSelected course for interaction (defaulting to first): {chosen_course['title']}")
        else:
             print("No course available to select.")
             return

        # 4. Interact with the chosen course
        if chosen_course and chosen_course.get("url"):
            await interact_with_course(page, chosen_course["url"])
        elif chosen_course:
             print(f"Chosen course '{chosen_course.get('title')}' is missing a URL.")
        else:
            # This case should be handled by the check after getting courses
            print("No course was chosen or available.")

        print("\nAgent finished interaction.")

    except Exception as e:
        print(f"\nAn error occurred in the main agent: {e}")
        # Save screenshot on error if page exists
        if page:
             try:
                 os.makedirs(couseraLogin.SCREENSHOT_DIR, exist_ok=True)
                 await page.screenshot(path=os.path.join(couseraLogin.SCREENSHOT_DIR, "agent_error_page.png"))
                 print("Screenshot saved on error.")
             except Exception as ss_error:
                  print(f"Could not save screenshot on error: {ss_error}")
    finally:
        print("Cleaning up agent resources...")
        # Fix: context.pages is a property, not a callable
        # Fix: proper checking for tracing.is_enabled() method
        if context:
            try:
                # Get pages as a property, not by calling it
                pages = context.pages
                if pages and len(pages) > 0:  # Check if there are pages
                    try:
                        # Check if tracing is enabled and has the is_enabled method
                        tracing_attr = getattr(context, 'tracing', None)
                        if tracing_attr and hasattr(tracing_attr, 'is_enabled'):
                            if await tracing_attr.is_enabled():
                                try:
                                    await context.tracing.stop(path=os.path.join(couseraLogin.TRACING_DIR, "coursera_agent_trace.zip"))
                                    print("Tracing stopped.")
                                except Exception as trace_error:
                                    print(f"Error stopping tracing: {trace_error}")
                    except Exception as tracing_error:
                        print(f"Error checking tracing status: {tracing_error}")
            except Exception as context_error:
                print(f"Error checking context pages: {context_error}")
                
        if browser:
            try:
                await browser.close()
                print("Browser closed.")
            except Exception as browser_error:
                print(f"Error closing browser: {browser_error}")
                
        # Ensure playwright stops if it was started
        if playwright and playwright._impl_obj._was_started:
             try:
                 await playwright.stop()
                 print("Playwright stopped.")
             except Exception as pw_error:
                 print(f"Error stopping playwright: {pw_error}")


if __name__ == "__main__":
    # Make sure directories exist (using paths from imported module)
    os.makedirs(couseraLogin.SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(couseraLogin.TRACING_DIR, exist_ok=True)

    print("Starting Coursera AI Agent...")
    # Check for API key before running async loop
    if 'GEMINI_API_KEY' not in os.environ:
        print("Critical Error: GEMINI_API_KEY environment variable is not set.")
    else:
        asyncio.run(main_agent())
