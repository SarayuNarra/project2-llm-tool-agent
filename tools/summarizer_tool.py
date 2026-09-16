from llm import llm


def summarizer_tool(text: str, question: str = "") -> str:
    """
    Generate a concise answer from tool information.

    For direct summarization requests, the user-provided text
    is summarized using the LLM.
    """

    prompt = f"""
You are a concise summarization assistant.

USER REQUEST:
{question}

TEXT TO SUMMARIZE:
{text}

Instructions:
- Return only the summarized answer.
- Keep the original meaning.
- Do not add facts.
- Do not mention tools.
- Do not mention the agent.
- Do not add headings.
- Keep it to 1 or 2 sentences.
"""

    response = llm.invoke(prompt)

    if response is None:
        return ""

    content = getattr(response, "content", "")

    if not content:
        return ""

    return str(content).strip()