import requests

from playwright.sync_api import sync_playwright

from agent.failure_analyzer import analyze_failure


# ========================================
# Normal test data
# ========================================

TEST_DATA = {

    "valid_login": {
        "username": "testuser",
        "password": "password123"
    },

    "invalid_password": {
        "username": "testuser",
        "password": "wrongpassword"
    },

    "invalid_username": {
        "username": "invaliduser",
        "password": "password123"
    }
}


# ========================================
# Edge-case test data
# ========================================

EDGE_TEST_DATA = {

    "empty_username": {
        "username": "",
        "password": "password123"
    },

    "empty_password": {
        "username": "testuser",
        "password": ""
    },

    "both_empty": {
        "username": "",
        "password": ""
    },

    "whitespace_username": {
        "username": "   ",
        "password": "password123"
    },

    "whitespace_password": {
        "username": "testuser",
        "password": "   "
    },

    "long_username": {
        "username": "a" * 256,
        "password": "password123"
    },

    "long_password": {
        "username": "testuser",
        "password": "p" * 256
    },

    "special_characters_username": {
        "username": "!@#$%^&*()",
        "password": "password123"
    }
}


# ========================================
# Combined test data
# ========================================

ALL_TEST_DATA = {
    **TEST_DATA,
    **EDGE_TEST_DATA
}


# ========================================
# API login test
# ========================================

def run_login_test(scenario):

    if scenario not in ALL_TEST_DATA:
        raise ValueError(
            f"Unknown test scenario: {scenario}"
        )

    test_data = ALL_TEST_DATA[scenario]

    username = test_data["username"]
    password = test_data["password"]

    url = "http://127.0.0.1:5000/login"

    try:

        response = requests.post(
            url,
            data={
                "username": username,
                "password": password
            },
            timeout=5
        )

        return {
            "execution_status": "EXECUTED",

            "scenario": scenario,

            "request": {
                "method": "POST",
                "endpoint": "/login"
            },

            "status_code": response.status_code,

            "response": response.text,

            "test_data": {
                "username": username,
                "password": password
            }
        }

    except requests.exceptions.ConnectionError:

        return {
            "execution_status": "BLOCKED",

            "scenario": scenario,

            "error": "Application is not reachable."
        }

    except requests.exceptions.Timeout:

        return {
            "execution_status": "ERROR",

            "scenario": scenario,

            "error": "Application request timed out."
        }

    except requests.exceptions.RequestException as error:

        return {
            "execution_status": "ERROR",

            "scenario": scenario,

            "error": str(error)
        }


# ========================================
# Browser login test
# ========================================

def run_browser_login_test(scenario):

    if scenario not in ALL_TEST_DATA:
        raise ValueError(
            f"Unknown test scenario: {scenario}"
        )

    test_data = ALL_TEST_DATA[scenario]

    username = test_data["username"]
    password = test_data["password"]

    url = "http://127.0.0.1:5000"

    screenshot_path = (
        f"browser_{scenario}.png"
    )

    try:

        with sync_playwright() as playwright:

            browser = playwright.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                url,
                wait_until="networkidle"
            )

            page.fill(
                'input[name="username"]',
                username
            )

            page.fill(
                'input[name="password"]',
                password
            )

            page.click("button")

            page.wait_for_load_state(
                "networkidle"
            )

            actual_page_text = page.locator(
                "body"
            ).inner_text()

            page.screenshot(
                path=screenshot_path,
                full_page=True
            )

            browser.close()

        return {
            "execution_status": "EXECUTED",

            "scenario": scenario,

            "browser": "Chromium",

            "request": {
                "method": "POST",
                "endpoint": "/login"
            },

            "actual_page_text": actual_page_text,

            "screenshot": screenshot_path,

            "test_data": {
                "username": username,
                "password": password
            }
        }

    except Exception as error:

        return {
            "execution_status": "ERROR",

            "scenario": scenario,

            "browser": "Chromium",

            "error": str(error)
        }


# ========================================
# Failure investigation
# ========================================

def investigate_failure(test_case, actual_result):

    return analyze_failure(
        test_case,
        actual_result
    )


# ========================================
# Read application source code
# ========================================

def read_application_code():

    file_path = "app/main.py"

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        code = file.read()

    return code