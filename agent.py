import json
import os
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["FOUNDRY_BASE_URL"],
    api_key=os.environ["FOUNDRY_API_KEY"],
    timeout=45.0,
    max_retries=2,
)

MODEL = os.environ["FOUNDRY_MODEL"]

SYSTEM_PROMPT = """
You are an enterprise AI technical assistant.

Your responsibilities:
1. Answer technical questions clearly.
2. Explain Python, Docker, cloud and AI concepts.
3. Use the calculator tool for arithmetic calculations.
4. Provide examples where helpful.
5. Never invent tool execution results.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform basic arithmetic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                    "operation": {
                        "type": "string",
                        "enum": [
                            "add",
                            "subtract",
                            "multiply",
                            "divide"
                        ]
                    }
                },
                "required": ["a", "b", "operation"],
                "additionalProperties": False
            }
        }
    }
]


def calculate(a, b, operation):
    a = Decimal(str(a))
    b = Decimal(str(b))

    if operation == "add":
        return str(a + b)

    if operation == "subtract":
        return str(a - b)

    if operation == "multiply":
        return str(a * b)

    if operation == "divide":
        if b == 0:
            return "Error: division by zero"
        return str(a / b)

    return "Unsupported operation"


def run_agent(history):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history
    ]

    for _ in range(5):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or "No response generated."

        messages.append(message.model_dump(
            exclude_none=True
        ))

        for tool_call in message.tool_calls:
            try:
                if tool_call.function.name != "calculate":
                    raise ValueError("Unknown tool")

                args = json.loads(
                    tool_call.function.arguments
                )

                result = calculate(
                    args["a"],
                    args["b"],
                    args["operation"]
                )

            except (
                ValueError,
                KeyError,
                TypeError,
                InvalidOperation
            ) as exc:
                result = f"Tool error: {exc}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "Tool execution limit reached."