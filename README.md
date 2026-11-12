# Step 1:  Create the project folder
```bash
mkdir ai-foundary-deploy
cd ai-foundary-deploy

python -m venv .venv
.\.venv\Scripts\activate
```


# Step 2: Create Project Structure
```bash
foundry-streamlit-agent/
│
├── app.py
├── agent.py
├── test_model.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
└── compose.yaml
```


# Step 3: create `requirements.txt`


```bash
streamlit
openai
python-dotenv
```

install the dependenices
```bash
pip install -r requirements.txt
```

# Step 4: Create `.env`

```python
FOUNDRY_BASE_URL=https://YOUR-RESOURCE.openai.azure.com/openai/v1/
FOUNDRY_API_KEY=YOUR_ACTUAL_API_KEY
FOUNDRY_MODEL=gpt-5.2
```

create `.gitignore`
```python
.env
.venv/
__pycache__/
*.pyc
```


# Step 5: test the foundary GET endpoint from python

create `test_model.py`

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["FOUNDRY_BASE_URL"],
    api_key=os.environ["FOUNDRY_API_KEY"]
)

response = client.chat.completions.create(
    model=os.environ["FOUNDRY_MODEL"],
    messages=[
        {
            "role": "system",
            "content": "You are a helpful technical assistant."
        },
        {
            "role": "user",
            "content": "Explain Docker in two sentences."
        }
    ]
)

print(response.choices[0].message.content)
```

```bash
python test_model.py
```

# Step 6: Build a Python AI agent with tool calling

create `agent.py`

```python
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
```


# Step 7: Build the Streamlit chat interface

create `app.py`

```python
import streamlit as st
from agent import run_agent, MODEL

st.set_page_config(
    page_title="Foundry AI Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Enterprise AI Agent")
st.caption(f"Powered by Microsoft Foundry | {MODEL}")

with st.sidebar:
    st.header("Agent Settings")
    st.success("Foundry configuration loaded")

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.write("Capabilities")
    st.write("• Technical Q&A")
    st.write("• Calculator tool")
    st.write("• Multi-turn conversations")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask your AI agent...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                response = run_agent(
                    st.session_state.messages
                )
                st.markdown(response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

            except Exception:
                st.error(
                    "Unable to contact the AI model. "
                    "Check the application logs."
                )
```

```bash
streamlit run app.py
```


# Step 8: Containerize the AI agent with docker

create `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir \
    -r requirements.txt

COPY app.py .
COPY agent.py .

RUN useradd --create-home appuser

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s \
  --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]

```