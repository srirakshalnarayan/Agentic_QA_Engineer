import os
import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ========================================
# Analyze a failed test
# ========================================

def analyze_failure(test_case, actual_result):

    prompt = f"""
You are an experienced software QA engineer.

You are investigating a failed software test.

TEST CASE:
{json.dumps(test_case, indent=2)}

ACTUAL APPLICATION RESULT:
{json.dumps(actual_result, indent=2)}

Your job is to determine why the test failed.

IMPORTANT RULES:

1. Clearly separate confirmed facts from assumptions.

2. Do not claim that test input values were
returned by the application.

3. Do not claim that a security issue exists
unless the evidence supports it.

4. Do not invent database, middleware, network,
authentication, or configuration problems.

5. Source-code evidence is included when available.
Use it to confirm the root cause.

6. If the available evidence does not confirm
the root cause, say:
"Root cause not confirmed."

7. Do not suggest a root cause merely because
it is a common software bug.

8. Keep the investigation concise.

Return exactly these sections:

CONFIRMED FACTS:
- What the test proves.

EXPECTED BEHAVIOR:
- What should have happened.

ACTUAL BEHAVIOR:
- What the application actually returned.

ROOT CAUSE:
- The confirmed root cause if the evidence supports it.
- Otherwise say "Root cause not confirmed."

SEVERITY:
- Low, Medium, High, or Critical.
- Give one short reason.

RECOMMENDED ACTION:
- What the developer should fix or investigate.
"""

    response = client.responses.create(

        model="gpt-5.6-luna",

        input=prompt
    )

    return response.output_text