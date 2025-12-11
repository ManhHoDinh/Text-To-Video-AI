import json
import re

def extract_json(text):
    # Remove dangerous control characters
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)

    # Extract first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response")

    json_str = match.group(0)

    # Common JSON fixes
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)
    json_str = json_str.replace('\\"', '"')

    return json.loads(json_str)
