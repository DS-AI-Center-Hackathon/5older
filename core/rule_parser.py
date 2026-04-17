import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a file organization rule parser.
Given a user's natural-language rule for organizing files, output ONLY a JSON object with this exact structure:
{
  "naming_pattern": "<description of how to name files, e.g. YYYYMMDD_topic_source>",
  "folders": ["folder1", "folder2", ...],
  "notes": "<any extra instructions>"
}
Always include a catch-all folder named "기타" as the last entry.
Output only valid JSON, no markdown, no explanation."""


def parse_rules(user_input: str, client: OpenAI) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)
