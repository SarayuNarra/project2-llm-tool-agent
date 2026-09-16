from schemas.planner_schema import Tool
from nodes.search import search_node
from nodes.calculator import calculator_node
from nodes.summarizer import summarizer_node
from nodes.rag import rag_node
from nodes.weather import weather_node
from nodes.translator import translator_node
from nodes.maps import maps_node

TOOL_REGISTRY = {
    Tool.SEARCH.value: {
        "node": search_node,
        "description": (
            "Search the internet for current or factual information."
        ),
        "requires_llm": False,
        "requires_summarization": True,
        "max_retries": 3,
    },
    Tool.CALCULATOR.value: {
        "node": calculator_node,
        "description": (
            "Perform mathematical calculations."
        ),
        "requires_llm": False,
        "requires_summarization": False,
        "max_retries": 3,
    },
    Tool.SUMMARIZER.value: {
        "node": summarizer_node,
        "description": (
            "Summarize retrieved information into a concise answer."
        ),
        "requires_llm": True,
        "max_retries": 3,
    },
    Tool.RAG.value: {
        "node": rag_node,
        "description": (
            "Retrieve relevant information from uploaded documents."
        ),
        "requires_llm": False,
        "requires_summarization": True,
        "max_retries": 3,
    },
    Tool.WEATHER.value: {
        "node": weather_node,
        "description":(
            "Get current weather information for a specific location.",
        ),
        "requires_llm": False,
        "requires_summarization": False,
        "max_retries": 3,
    },
    Tool.TRANSLATOR.value: {
       "node": translator_node,
       "description":(
           "Translate text into a requested language.",
       ), 
       "requires_llm": True,
       "requires_summarization": False,
       "max_retries": 3,
    },
    Tool.MAPS.value: {
    "node": maps_node,
    "description": (
        "Find routes, distances, and travel "
        "duration between locations."
    ),
    "requires_llm": False,
    "requires_summarization": False,
    "max_retries": 3,
    },
}