import os
from openai import OpenAI
import json
from utility.script.json_safeguard import extract_json

if len(os.environ.get("GROQ_API_KEY")) > 30:
    from groq import Groq
    model = "llama-3.1-8b-instant"  # UPDATED MODEL
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
        )
else:
    OPENAI_API_KEY = os.getenv('OPENAI_KEY')
    model = "gpt-4o"
    client = OpenAI(api_key=OPENAI_API_KEY)

def generate_script(topic):
    prompt = (
        """You are a seasoned content writer for a YouTube Shorts channel, specializing in facts videos. 
        Your facts shorts are concise, each lasting less than 50 seconds (approximately 140 words). 
        They are incredibly engaging and original. When a user requests a specific type of facts short, you will create it.

        Keep it brief, highly interesting, and unique.

        Strictly output the script in a JSON format:
        {"script": "Here is the script ..."}
        """
    )

    response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": topic}
            ]
        )

    content = response.choices[0].message.content
    data = extract_json(content)
    return data["script"].strip()
    try:
        return json.loads(content)["script"]
    except Exception:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        cleaned = content[json_start:json_end]
        return json.loads(cleaned)["script"]
