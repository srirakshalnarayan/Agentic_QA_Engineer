import os
import json
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

from agent.tools import (
    run_login_test,
    run_browser_login_test,
    investigate_failure,
    read_application_code
)

from agent.test_ai import (
    generate_test_cases,
    validate_test_cases,
    generate_edge_cases,
    validate_edge_cases
)


# ========================================
# LOAD ENVIRONMENT
# ========================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ========================================
# QA GOAL
# ========================================

qa_goal = """
Test the ShopEasy login functionality.

Users should be able to log in using valid credentials.
Users should be rejected when they provide an incorrect password.
Users should be rejected when they provide an invalid username.

The login user interface should also be tested.

The QA agent should also consider unusual,
boundary, and edge-case inputs.
"""


# ========================================
# GENERATE NORMAL TEST CASES
# ========================================

print("\nGenerating normal test cases...")

test_cases = generate_test_cases(
    qa_goal
)

validate_test_cases(
    test_cases
)

print(
    "AI generated",
    len(test_cases),
    "normal test scenarios."
)


# ========================================
# GENERATE EDGE CASES
# ========================================

print("\nGenerating edge cases...")

edge_cases = generate_edge_cases(
    qa_goal
)

validate_edge_cases(
    edge_cases
)

print(
    "AI generated",
    len(edge_cases),
    "edge-case scenarios."
)


# ========================================
# COMBINE TEST SUITE
# ========================================

all_tests = (
    test_cases +
    edge_cases
)

print(
    "\nTotal test scenarios:",
    len(all_tests)
)


# ========================================
# TEST STRATEGY PLANNER
# ========================================

def create_test_plan(test_cases):

    test_summary = []

    for test in test_cases:

        test_summary.append({

            "id": test["id"],

            "title": test["title"],

            "scenario": test["scenario"],

            "expected_result": (
                test["expected_result"]
            ),

            "priority": test["priority"]
        })


    response = client.responses.create(

        model="gpt-5.6-luna",

        input=f"""
You are a software QA test planner.

QA GOAL:
{qa_goal}

TEST SUITE:
{json.dumps(test_summary, indent=2)}

Choose the best execution strategy for every test.

Available strategies:

api
- Directly tests the backend login endpoint.
- Best for backend behavior, validation,
  boundary inputs, and data-driven tests.

browser
- Tests the actual ShopEasy UI through Chromium.
- Best when UI behavior needs to be verified.

Rules:

1. Return exactly one strategy for every test.
2. Use the exact test ID.
3. Strategy must be "api" or "browser".
4. Do not invent test IDs.
5. Do not include usernames or passwords.
6. Consider the test scenario when choosing.
7. Return ONLY valid JSON.

Format:

[
    {{
        "test_id": "TC-001",
        "strategy": "browser"
    }}
]
"""
    )


    plan = json.loads(
        response.output_text
    )

    return plan


# ========================================
# VALIDATE TEST PLAN
# ========================================

def validate_test_plan(
    plan,
    test_cases
):

    if not isinstance(plan, list):

        raise ValueError(
            "AI test plan must be a list."
        )


    expected_ids = {
        test["id"]
        for test in test_cases
    }


    returned_ids = {
        item.get("test_id")
        for item in plan
    }


    if expected_ids != returned_ids:

        raise ValueError(
            "AI test plan does not contain "
            "exactly the required test IDs."
        )


    for item in plan:

        if item.get("strategy") not in {
            "api",
            "browser"
        }:

            raise ValueError(
                f"Invalid testing strategy: "
                f"{item.get('strategy')}"
            )


    return True


# ========================================
# CREATE TEST PLAN
# ========================================

print(
    "\nAI is deciding the best testing "
    "strategy for each test..."
)


test_plan = create_test_plan(
    all_tests
)


validate_test_plan(
    test_plan,
    all_tests
)


print(
    "\nAI test strategy:"
)

print(
    json.dumps(
        test_plan,
        indent=2
    )
)


# ========================================
# STRATEGY LOOKUP
# ========================================

strategy_map = {

    item["test_id"]:
        item["strategy"]

    for item in test_plan
}


# ========================================
# RESULT STORAGE
# ========================================

results = []


# ========================================
# RESULT EVALUATOR
# ========================================

def evaluate_result(
    test_case,
    result
):

    execution_status = result.get(
        "execution_status"
    )


    # ------------------------------------
    # Application unavailable
    # ------------------------------------

    if execution_status == "BLOCKED":

        return "BLOCKED"


    # ------------------------------------
    # Technical execution problem
    # ------------------------------------

    if execution_status == "ERROR":

        return "ERROR"


    # ------------------------------------
    # Test executed
    # ------------------------------------

    if execution_status == "EXECUTED":

        expected = test_case[
            "expected_result"
        ]


        actual = result.get(
            "actual_page_text"
        )


        if actual is None:

            actual = result.get(
                "response",
                ""
            )


        actual = str(actual).strip()


        expected = str(
            expected
        ).strip()


        if actual == expected:

            return "PASS"


        return "FAIL"


    return "ERROR"


# ========================================
# EXECUTION ISSUE EXPLANATION
# ========================================

def explain_execution_issue(
    status,
    result
):

    error = result.get(
        "error",
        "No additional error information was provided."
    )


    if status == "BLOCKED":

        return {

            "reason": error,

            "recommendation": (
                "Resolve the blocking condition "
                "and rerun the test."
            )
        }


    if status == "ERROR":

        return {

            "reason": error,

            "recommendation": (
                "Check the test execution environment, "
                "application behavior, browser state, "
                "and reported error."
            )
        }


    return {

        "reason": (
            "Unknown execution problem."
        ),

        "recommendation": (
            "Review the test execution logs."
        )
    }


# ========================================
# BUILD TEST EVIDENCE
# ========================================

def build_evidence(
    test,
    strategy,
    actual_result
):

    evidence = {

        "test_id": test["id"],

        "title": test["title"],

        "scenario": test["scenario"],

        "strategy": strategy,

        "expected_result": (
            test["expected_result"]
        ),

        "execution_status": (
            actual_result.get(
                "execution_status"
            )
        )
    }


    if "status_code" in actual_result:

        evidence["status_code"] = (
            actual_result["status_code"]
        )


    if "response" in actual_result:

        evidence["actual_result"] = (
            actual_result["response"]
        )


    if "actual_page_text" in actual_result:

        evidence["actual_result"] = (
            actual_result["actual_page_text"]
        )


    if "browser" in actual_result:

        evidence["browser"] = (
            actual_result["browser"]
        )


    if "request" in actual_result:

        evidence["request"] = (
            actual_result["request"]
        )


    if "screenshot" in actual_result:

        evidence["screenshot"] = (
            actual_result["screenshot"]
        )


    if "error" in actual_result:

        evidence["error"] = (
            actual_result["error"]
        )


    return evidence


# ========================================
# RUN ALL TESTS
# ========================================

for test in all_tests:

    print("\n================================")
    print(
        "Test:",
        test["id"]
    )

    print(
        "Title:",
        test["title"]
    )

    print(
        "Scenario:",
        test["scenario"]
    )

    print("================================")


    # ====================================
    # GET STRATEGY
    # ====================================

    strategy = strategy_map[
        test["id"]
    ]


    print(
        "\nSelected strategy:",
        strategy
    )


    # ====================================
    # EXECUTE API
    # ====================================

    if strategy == "api":

        print(
            "Executing API test:",
            test["scenario"]
        )

        actual_result = run_login_test(
            test["scenario"]
        )


    # ====================================
    # EXECUTE BROWSER
    # ====================================

    elif strategy == "browser":

        print(
            "Executing browser test:",
            test["scenario"]
        )

        actual_result = run_browser_login_test(
            test["scenario"]
        )


    else:

        actual_result = {

            "execution_status": "ERROR",

            "error": (
                "Invalid testing strategy."
            )
        }


    # ====================================
    # BUILD EVIDENCE
    # ====================================

    evidence = build_evidence(

        test,

        strategy,

        actual_result

    )


    print(
        "\nExecution evidence:"
    )

    print(
        json.dumps(
            evidence,
            indent=2
        )
    )


    # ====================================
    # EVALUATE RESULT
    # ====================================

    status = evaluate_result(

        test,

        actual_result

    )


    print(
        "\nDetermined status:",
        status
    )


    # ====================================
    # PASS
    # ====================================

    if status == "PASS":

        results.append({

            "test_id": test["id"],

            "title": test["title"],

            "scenario": test["scenario"],

            "strategy": strategy,

            "status": "PASS",

            "expected_result": (
                test["expected_result"]
            ),

            "actual_result": (
                evidence.get(
                    "actual_result",
                    ""
                )
            ),

            "evidence": evidence,

            "reason": (
                "Expected behavior matched "
                "the actual application behavior."
            ),

            "recommendation": (
                "No action required."
            )
        })

        continue


    # ====================================
    # ERROR / BLOCKED
    # ====================================

    if status in {
        "ERROR",
        "BLOCKED"
    }:

        issue = explain_execution_issue(

            status,

            actual_result

        )


        results.append({

            "test_id": test["id"],

            "title": test["title"],

            "scenario": test["scenario"],

            "strategy": strategy,

            "status": status,

            "expected_result": (
                test["expected_result"]
            ),

            "actual_result": (
                evidence.get(
                    "actual_result",
                    ""
                )
            ),

            "evidence": evidence,

            "reason": issue[
                "reason"
            ],

            "recommendation": issue[
                "recommendation"
            ]
        })

        continue


    # ====================================
    # FAIL
    # ====================================

    if status == "FAIL":

        print(
            "\nTest failed."
        )


        print(
            "Collecting application source "
            "for investigation..."
        )


        # =================================
        # READ SOURCE CODE
        # =================================

        source_code = (
            read_application_code()
        )


        # =================================
        # ADD SOURCE TO EVIDENCE
        # =================================

        investigation_evidence = {

            **evidence,

            "source_code": source_code
        }


        print(
            "Sending failure evidence "
            "to AI..."
        )


        # =================================
        # AI INVESTIGATION
        # =================================

        investigation = investigate_failure(

            test,

            investigation_evidence

        )


        print(
            "\nInvestigation result:"
        )

        print(
            investigation
        )


        # =================================
        # CREATE BUG REPORT
        # =================================

        bug_number = (
            sum(
                1
                for result in results
                if result["status"] == "FAIL"
            )
            + 1
        )


        bug_id = (
            f"BUG-{bug_number:03d}"
        )


        bug_report = {

            "bug_id": bug_id,

            "title": test["title"],

            "test_id": test["id"],

            "scenario": test["scenario"],

            "strategy": strategy,

            "severity": "High",

            "expected_result": (
                test["expected_result"]
            ),

            "actual_result": (
                evidence.get(
                    "actual_result",
                    ""
                )
            ),

            "root_cause": investigation,

            "recommendation": (
                "Review the identified root cause "
                "and implement the recommended fix."
            )
        }


        print(
            "\nBug report:"
        )

        print(
            json.dumps(
                bug_report,
                indent=2
            )
        )


        # =================================
        # SAVE FAILURE RESULT
        # =================================

        results.append({

            "test_id": test["id"],

            "title": test["title"],

            "scenario": test["scenario"],

            "strategy": strategy,

            "status": "FAIL",

            "expected_result": (
                test["expected_result"]
            ),

            "actual_result": (
                evidence.get(
                    "actual_result",
                    ""
                )
            ),

            "evidence": evidence,

            "investigation": investigation,

            "bug_report": bug_report,

            "reason": (
                "Expected behavior did not "
                "match actual behavior."
            ),

            "recommendation": (
                "Review the identified root cause "
                "and implement the recommended fix."
            )
        })


# ========================================
# CALCULATE SUMMARY
# ========================================

total = len(results)


passed = sum(
    1
    for result in results
    if result["status"] == "PASS"
)


failed = sum(
    1
    for result in results
    if result["status"] == "FAIL"
)


errors = sum(
    1
    for result in results
    if result["status"] == "ERROR"
)


blocked = sum(
    1
    for result in results
    if result["status"] == "BLOCKED"
)


bugs = [

    result["bug_report"]

    for result in results

    if "bug_report" in result
]


# ========================================
# BUILD FINAL REPORT
# ========================================

timestamp = datetime.now().isoformat()


final_report = {

    "project": "Agentic QA Engineer",

    "application": "ShopEasy",

    "generated_at": timestamp,

    "qa_goal": qa_goal.strip(),

    "summary": {

        "total_tests": total,

        "passed": passed,

        "failed": failed,

        "errors": errors,

        "blocked": blocked,

        "bugs_found": len(bugs)
    },

    "tests": results,

    "bugs": bugs
}


# ========================================
# CREATE REPORT DIRECTORY
# ========================================

os.makedirs(
    "reports",
    exist_ok=True
)


# ========================================
# SAVE JSON REPORT
# ========================================

json_report_path = (
    "reports/qa_report.json"
)


with open(
    json_report_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        final_report,
        file,
        indent=4
    )


# ========================================
# BUILD MARKDOWN REPORT
# ========================================

markdown = []


markdown.append(
    "# ShopEasy QA Report"
)

markdown.append("")

markdown.append(
    f"Generated: {timestamp}"
)

markdown.append("")

markdown.append(
    "## Summary"
)

markdown.append("")

markdown.append(
    f"- Total tests: {total}"
)

markdown.append(
    f"- PASS: {passed}"
)

markdown.append(
    f"- FAIL: {failed}"
)

markdown.append(
    f"- ERROR: {errors}"
)

markdown.append(
    f"- BLOCKED: {blocked}"
)

markdown.append(
    f"- Bugs found: {len(bugs)}"
)

markdown.append("")


# ========================================
# TEST RESULTS
# ========================================

markdown.append(
    "## Test Results"
)

markdown.append("")


markdown.append(
    "| Test | Scenario | Strategy | Status |"
)

markdown.append(
    "|---|---|---|---|"
)


for result in results:

    markdown.append(

        "| "
        + result["test_id"]
        + " | "
        + result["scenario"]
        + " | "
        + result["strategy"]
        + " | "
        + result["status"]
        + " |"

    )


markdown.append("")


# ========================================
# BUG REPORTS
# ========================================

markdown.append(
    "## Bugs Found"
)

markdown.append("")


if not bugs:

    markdown.append(
        "No bugs were detected."
    )


else:

    for bug in bugs:

        markdown.append(
            f"### {bug['bug_id']}"
        )

        markdown.append("")

        markdown.append(
            f"**Title:** {bug['title']}"
        )

        markdown.append("")

        markdown.append(
            f"**Severity:** {bug['severity']}"
        )

        markdown.append("")

        markdown.append(
            f"**Test:** {bug['test_id']}"
        )

        markdown.append("")

        markdown.append(
            f"**Scenario:** {bug['scenario']}"
        )

        markdown.append("")

        markdown.append(
            "#### Expected"
        )

        markdown.append("")

        markdown.append(
            str(
                bug["expected_result"]
            )
        )

        markdown.append("")

        markdown.append(
            "#### Actual"
        )

        markdown.append("")

        markdown.append(
            str(
                bug["actual_result"]
            )
        )

        markdown.append("")

        markdown.append(
            "#### AI Investigation"
        )

        markdown.append("")

        markdown.append(
            str(
                bug["root_cause"]
            )
        )

        markdown.append("")

        markdown.append(
            "#### Recommended Action"
        )

        markdown.append("")

        markdown.append(
            bug["recommendation"]
        )

        markdown.append("")


# ========================================
# SAVE MARKDOWN REPORT
# ========================================

markdown_report_path = (
    "reports/qa_report.md"
)


with open(
    markdown_report_path,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(markdown)
    )


# ========================================
# FINAL TERMINAL REPORT
# ========================================

print("\n")
print("================================")
print("FINAL QA REPORT")
print("================================")


print(
    "Application:",
    "ShopEasy"
)


print(
    "Total tests:",
    total
)


print(
    "PASS:",
    passed
)


print(
    "FAIL:",
    failed
)


print(
    "ERROR:",
    errors
)


print(
    "BLOCKED:",
    blocked
)


print(
    "Bugs found:",
    len(bugs)
)


# ========================================
# BUG SUMMARY
# ========================================

if bugs:

    print(
        "\n================================"
    )

    print(
        "BUG SUMMARY"
    )

    print(
        "================================"
    )


    for bug in bugs:

        print(
            "\n",
            bug["bug_id"]
        )

        print(
            "Title:",
            bug["title"]
        )

        print(
            "Severity:",
            bug["severity"]
        )

        print(
            "Test:",
            bug["test_id"]
        )


# ========================================
# REPORT FILES
# ========================================

print(
    "\n================================"
)

print(
    "REPORTS SAVED"
)

print(
    "================================"
)

print(
    json_report_path
)

print(
    markdown_report_path
)


# ========================================
# COMPLETE
# ========================================

print(
    "\n================================"
)

print(
    "QA EXECUTION COMPLETE"
)

print(
    "================================"
)