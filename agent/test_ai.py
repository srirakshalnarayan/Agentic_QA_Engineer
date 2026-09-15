import os
import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def generate_test_cases(requirement):

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=f"""
You are a software QA engineer.

Read this requirement:

{requirement}

Generate exactly 3 test cases.

The three scenarios MUST be:

1. valid_login
2. invalid_password
3. invalid_username

Return ONLY valid JSON.

Return a list where every test case contains:

- id
- title
- scenario
- expected_result
- priority

Do NOT generate username or password.

The scenario MUST be exactly one of:

- valid_login
- invalid_password
- invalid_username

The expected_result MUST be exactly one of:

- Login successful
- Invalid username or password

Priority MUST be one of:

- High
- Medium
- Low
"""
    )

    test_cases = json.loads(
        response.output_text
    )

    return test_cases


def generate_edge_cases(requirement):

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=f"""
You are an experienced software QA engineer.

Read this requirement:

{requirement}

Think about unusual and boundary inputs that could
cause the login functionality to behave incorrectly.

Generate exactly 5 edge-case test scenarios.

Choose ONLY from these scenarios:

- empty_username
- empty_password
- both_empty
- whitespace_username
- whitespace_password
- long_username
- long_password
- special_characters_username

Choose the 5 most relevant scenarios.

Return ONLY valid JSON.

Return a list where every test case contains:

- id
- title
- scenario
- expected_result
- priority

Do NOT generate username or password values.

The scenario must be one of the allowed scenarios.

For all these edge cases, the expected result should be:

Invalid username or password

Priority must be one of:

- High
- Medium
- Low
"""
    )

    edge_cases = json.loads(
        response.output_text
    )

    # Give edge cases their own unique IDs.
    for index, test in enumerate(edge_cases, start=1):
        test["id"] = f"EDGE-{index:03d}"

    return edge_cases


def validate_test_cases(test_cases):

    if not isinstance(test_cases, list):
        raise ValueError("AI output must be a list.")

    if len(test_cases) != 3:
        raise ValueError("AI must generate exactly 3 test cases.")

    required_fields = {
        "id",
        "title",
        "scenario",
        "expected_result",
        "priority"
    }

    allowed_scenarios = {
        "valid_login",
        "invalid_password",
        "invalid_username"
    }

    allowed_results = {
        "Login successful",
        "Invalid username or password"
    }

    allowed_priorities = {
        "High",
        "Medium",
        "Low"
    }

    for test in test_cases:

        if not isinstance(test, dict):
            raise ValueError(
                "Each test case must be a dictionary."
            )

        missing_fields = (
            required_fields - set(test.keys())
        )

        if missing_fields:
            raise ValueError(
                f"Missing fields: {missing_fields}"
            )

        if test["scenario"] not in allowed_scenarios:
            raise ValueError(
                f"Invalid scenario: {test['scenario']}"
            )

        if test["expected_result"] not in allowed_results:
            raise ValueError(
                f"Invalid expected result: "
                f"{test['expected_result']}"
            )

        if test["priority"] not in allowed_priorities:
            raise ValueError(
                f"Invalid priority: {test['priority']}"
            )

    return True


def validate_edge_cases(edge_cases):

    if not isinstance(edge_cases, list):
        raise ValueError(
            "AI edge-case output must be a list."
        )

    if len(edge_cases) != 5:
        raise ValueError(
            "AI must generate exactly 5 edge cases."
        )

    required_fields = {
        "id",
        "title",
        "scenario",
        "expected_result",
        "priority"
    }

    allowed_scenarios = {
        "empty_username",
        "empty_password",
        "both_empty",
        "whitespace_username",
        "whitespace_password",
        "long_username",
        "long_password",
        "special_characters_username"
    }

    allowed_results = {
        "Invalid username or password"
    }

    allowed_priorities = {
        "High",
        "Medium",
        "Low"
    }

    for test in edge_cases:

        if not isinstance(test, dict):
            raise ValueError(
                "Each edge case must be a dictionary."
            )

        missing_fields = (
            required_fields - set(test.keys())
        )

        if missing_fields:
            raise ValueError(
                f"Missing fields: {missing_fields}"
            )

        if test["scenario"] not in allowed_scenarios:
            raise ValueError(
                f"Invalid edge-case scenario: "
                f"{test['scenario']}"
            )

        if test["expected_result"] not in allowed_results:
            raise ValueError(
                f"Invalid edge-case expected result: "
                f"{test['expected_result']}"
            )

        if test["priority"] not in allowed_priorities:
            raise ValueError(
                f"Invalid priority: "
                f"{test['priority']}"
            )

    return True


if __name__ == "__main__":

    requirement = """
    Users should be able to log in using valid credentials.
    Users should be rejected when they provide an incorrect password.
    Users should be rejected when they provide an invalid username.
    """

    print("\nGenerating normal test cases...")

    test_cases = generate_test_cases(requirement)
    validate_test_cases(test_cases)

    print(
        json.dumps(
            test_cases,
            indent=4
        )
    )

    print("\nGenerating edge cases...")

    edge_cases = generate_edge_cases(requirement)
    validate_edge_cases(edge_cases)

    print(
        json.dumps(
            edge_cases,
            indent=4
        )
    )