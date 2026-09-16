# AI Engineer Tool Agent

A multi-tool AI agent built with Python, LangGraph, LangChain, and Google Gemini. The system can understand a user's request, create a structured execution plan, route tasks to specialized tools, handle dependencies between tasks, execute independent tasks in parallel, and generate a natural-language response.

## Overview

This project was built to explore how production-oriented AI agents can be designed using graph-based orchestration rather than a simple single LLM call.

The agent follows a planning and execution workflow:

**User Query → Planner → Executor → Tools → Response**

The planner converts the user's request into structured steps using Pydantic models. The executor determines which tasks are ready to run based on their dependencies and routes them to the appropriate specialized tool.

## Key Features

- Structured task planning using Pydantic
- LangGraph-based workflow orchestration
- Dictionary-based tool registry for routing
- Sequential multi-step task execution
- Parallel execution of independent tasks
- Dependency resolution between tool outputs
- Retry handling for temporary failures
- Web search
- Mathematical calculations
- Current weather information
- Text translation
- Retrieval-Augmented Generation (RAG)
- Text summarization
- Maps and route planning
- Location clarification for ambiguous places
- Conversation continuation after clarification
- Natural-language final responses

## Supported Tools

| Tool | Purpose |
|---|---|
| Search | Retrieves current or external information from the web |
| Calculator | Performs mathematical calculations |
| Weather | Retrieves current weather information |
| Translator | Translates text into the requested language |
| RAG | Answers questions using uploaded documents |
| Summarizer | Summarizes and combines information |
| Maps | Finds routes and directions between locations |

## Architecture

```text
                         User Query
                              |
                              v
                       +-------------+
                       |   Planner   |
                       +-------------+
                              |
                              v
                   Structured Plan
                              |
                              v
                       +-------------+
                       |  Executor   |
                       +-------------+
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
           Search        Calculator          RAG
              |               |               |
              +---------------+---------------+
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
           Weather       Translator          Maps
                              |
                              v
                       +-------------+
                       |  Response   |
                       +-------------+
                              |
                              v
                         Final Answer


## Author

**Sarayu Narra**

B.Tech Artificial Intelligence  
SRM Institute of Science and Technology

---

⭐ Built as part of my journey toward becoming an AI Engineer.