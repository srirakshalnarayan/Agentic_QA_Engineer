# Agentic QA Engineer

An AI-powered QA agent that takes software requirements, generates test cases, decides how they should be tested, executes the tests, investigates failures, and produces structured QA reports.

## Overview

Software testing usually involves manually writing test cases, deciding which tests to run, executing them, and investigating failures.

This project explores how "Agentic AI can assist with that workflow".

The agent starts with a software requirement and works through multiple stages of the QA process. It uses AI for tasks that require reasoning, while Python handles the actual test execution and result evaluation.

The application used for testing is a small Flask-based login application called "ShopEasy".

The current workflow is:

     text
Software Requirement
        -
Generate Test Cases
        -
Generate Edge Cases
        -
Validate Test Cases
        -
Select API / Browser Strategy
        -
Execute Tests
        -
Collect Evidence
        -
PASS / FAIL / ERROR / BLOCKED
        -
Investigate Failures
        -
Generate Bug Reports
        -
Generate QA Reports
