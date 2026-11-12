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