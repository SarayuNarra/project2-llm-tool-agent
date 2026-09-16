from llm import llm

def translator_tool(
    text: str,
    target_language: str
):
    prompt = f"""
Translate the following text into {target_language}.
Rules:
- Preserve the original meaning.
- Do not add explanations.
- Return only the translated text.
- Keep technical terms accurate.
Text:
{text}
"""
    response = llm.invoke(prompt)
    return response.content.strip()