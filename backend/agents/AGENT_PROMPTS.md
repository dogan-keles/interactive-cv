# Agent Prompt Templates

This document defines the prompt contracts for all agents in the interactive CV system.

## Overview

All agents receive a `RequestContext` object containing:
- `user_query`: Original user text
- `profile_id`: Profile identifier (mandatory)
- `language`: Detected language (Language enum)
- `intent`: Detected intent (Intent enum)
- `rag_context`: Optional pre-retrieved RAG context

## Core Principles

1. **Language Compliance**: All responses must match `context.language`. Never override.
2. **Tool-Only Access**: Agents use tools, never access databases directly.
3. **No Routing Logic**: Agents don't detect intent or route requests.
4. **Role Focus**: Each agent has a specific domain and clear boundaries.

## Agent Prompts

### ProfileAgent

**Domain**: Skills, experience, background, general professional questions

**System Prompt**: `PROFILE_AGENT_SYSTEM_PROMPT`
**Instructions**: `PROFILE_AGENT_INSTRUCTIONS`

**Allowed Tools**:
- SQL-based profile tools
- Semantic search tools (RAG)

**Forbidden**:
- GitHub repository details
- CV file generation

**Example Usage**:
```python
from agents.prompts import PROFILE_AGENT_SYSTEM_PROMPT, PROFILE_AGENT_INSTRUCTIONS
from orchestrator.types import RequestContext

async def process(self, context: RequestContext) -> str:
    # Build prompt with system prompt + instructions + context
    prompt = f"{PROFILE_AGENT_SYSTEM_PROMPT}\n\n{PROFILE_AGENT_INSTRUCTIONS}"
    # Add context information
    prompt += f"\n\nUser Query: {context.user_query}"
    prompt += f"\nProfile ID: {context.profile_id}"
    prompt += f"\nLanguage: {context.language.value}"
    # Use tools to retrieve data, then call LLM
    ...
```

---

### GitHubAgent

**Domain**: GitHub projects, repositories, tech stack, code-related experience

**System Prompt**: `GITHUB_AGENT_SYSTEM_PROMPT`
**Instructions**: `GITHUB_AGENT_INSTRUCTIONS`

**Allowed Tools**:
- GitHub data tools
- Semantic search tools (with source_type=GITHUB)

**Forbidden**:
- General profile questions
- CV file generation

**Example Usage**:
```python
from agents.prompts import GITHUB_AGENT_SYSTEM_PROMPT, GITHUB_AGENT_INSTRUCTIONS

async def process(self, context: RequestContext) -> str:
    prompt = f"{GITHUB_AGENT_SYSTEM_PROMPT}\n\n{GITHUB_AGENT_INSTRUCTIONS}"
    # Add context and use GitHub tools
    ...
```

---

### CVAgent

**Domain**: CV generation, download links, CV formatting

**System Prompt**: `CV_AGENT_SYSTEM_PROMPT`
**Instructions**: `CV_AGENT_INSTRUCTIONS`

**Allowed Tools**:
- File storage tools
- Profile data tools

**Forbidden**:
- General career questions
- GitHub project discussions

**Example Usage**:
```python
from agents.prompts import CV_AGENT_SYSTEM_PROMPT, CV_AGENT_INSTRUCTIONS

async def process(self, context: RequestContext) -> str:
    prompt = f"{CV_AGENT_SYSTEM_PROMPT}\n\n{CV_AGENT_INSTRUCTIONS}"
    # Use file storage and profile tools
    ...
```

---

### GuardrailAgent

**Domain**: Out-of-scope queries, unsupported requests

**System Prompt**: `GUARDRAIL_AGENT_SYSTEM_PROMPT`
**Instructions**: `GUARDRAIL_AGENT_INSTRUCTIONS`

**Behavior**:
- Polite decline
- Suggest what system CAN help with
- Maintain helpful tone

**Example Usage**:
```python
from agents.prompts import GUARDRAIL_AGENT_SYSTEM_PROMPT, GUARDRAIL_AGENT_INSTRUCTIONS

async def handle_out_of_scope(self, context: RequestContext) -> str:
    prompt = f"{GUARDRAIL_AGENT_SYSTEM_PROMPT}\n\n{GUARDRAIL_AGENT_INSTRUCTIONS}"
    # Generate polite decline message
    ...
```

---

## Language Handling

All prompts include language instructions. Use `get_language_instruction()` for additional language-specific guidance:

```python
from agents.prompts import get_language_instruction
from orchestrator.types import Language

instruction = get_language_instruction(context.language)
# Adds: "Respond in English" or "Yanıtınızı Türkçe olarak verin"
```

## Prompt Construction Pattern

```python
def build_agent_prompt(
    system_prompt: str,
    instructions: str,
    context: RequestContext,
    additional_context: Optional[str] = None,
) -> str:
    """Build complete prompt for agent."""
    prompt = f"{system_prompt}\n\n{instructions}"
    prompt += f"\n\nUser Query: {context.user_query}"
    prompt += f"\nProfile ID: {context.profile_id}"
    prompt += f"\nLanguage: {context.language.value}"
    
    if context.rag_context:
        prompt += f"\n\nRetrieved Context:\n{context.rag_context}"
    
    if additional_context:
        prompt += f"\n\nAdditional Context:\n{additional_context}"
    
    return prompt
```

## Tool Usage

Agents must use tools for all data access:

```python
# RAG retrieval
from tools.semantic_search_tools import semantic_search_with_context

context_text = await semantic_search_with_context(
    query=context.user_query,
    profile_id=context.profile_id,
    retrieval_pipeline=self.retrieval_pipeline,
    top_k=5,
)

# SQL profile queries
from tools.profile_tools import get_profile_skills

skills = await get_profile_skills(
    profile_id=context.profile_id,
)
```

## Testing Prompts

When testing agents:
1. Verify language compliance (response matches context.language)
2. Verify tool usage (no direct DB access)
3. Verify role boundaries (agent stays in domain)
4. Verify redirect behavior (polite redirects to other agents)

## Maintenance

- Keep prompts minimal and deterministic
- Avoid business logic in prompts
- Focus on role and behavior
- Update prompts when agent responsibilities change
- Document any prompt changes in this file





