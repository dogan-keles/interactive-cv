# Orchestrator Usage Examples

## Basic Usage

```python
from orchestrator import Orchestrator, RequestContext
from agents.profile_agent import ProfileAgent
from agents.github_agent import GitHubAgent
from agents.cv_agent import CVAgent
from agents.guardrail_agent import GuardrailAgent

# Initialize agents
profile_agent = ProfileAgent()
github_agent = GitHubAgent()
cv_agent = CVAgent()
guardrail_agent = GuardrailAgent()

# Initialize orchestrator
orchestrator = Orchestrator(
    profile_agent=profile_agent,
    github_agent=github_agent,
    cv_agent=cv_agent,
    guardrail_agent=guardrail_agent,
)

# Process request
response = await orchestrator.process_request(
    user_query="What is Doğan's Python experience?",
    profile_id=1,
)
# Response will be in English (detected automatically)
```

## Language Detection Examples

### Turkish Input
```python
# Turkish query
response = await orchestrator.process_request(
    user_query="Doğan'ın Python deneyimi nedir?",
    profile_id=1,
)
# Language: Turkish (detected)
# Response: "Doğan'ın Python konusunda 5 yıllık deneyimi var..."
```

### English Input
```python
# English query
response = await orchestrator.process_request(
    user_query="What is Doğan's Python experience?",
    profile_id=1,
)
# Language: English (detected)
# Response: "Doğan has 5 years of experience with Python..."
```

### Mixed Language Input
```python
# Mixed Turkish/English
response = await orchestrator.process_request(
    user_query="Doğan'ın GitHub projects hakkında bilgi ver",
    profile_id=1,
)
# Language: Turkish (detected via Turkish keywords)
# Intent: GITHUB_INFO
# Response: "Doğan'ın GitHub'da birkaç projesi var..."
```

## Intent Routing Examples

### Profile Info Intent
```python
# Profile-related query
response = await orchestrator.process_request(
    user_query="What skills does Doğan have?",
    profile_id=1,
)
# Intent: PROFILE_INFO
# Agent: ProfileAgent
```

### GitHub Info Intent
```python
# GitHub-related query
response = await orchestrator.process_request(
    user_query="Show me Doğan's GitHub projects",
    profile_id=1,
)
# Intent: GITHUB_INFO
# Agent: GitHubAgent
```

### CV Request Intent
```python
# CV-related query
response = await orchestrator.process_request(
    user_query="I want to download the CV",
    profile_id=1,
)
# Intent: CV_REQUEST
# Agent: CVAgent
```

### Out-of-Scope Intent
```python
# Irrelevant query
response = await orchestrator.process_request(
    user_query="What's the weather today?",
    profile_id=1,
)
# Intent: OUT_OF_SCOPE
# Agent: GuardrailAgent
# Response: "I can only answer questions about the candidate's profile..."
```

## With RAG Context

```python
# Pre-retrieve RAG context
from tools.semantic_search_tools import semantic_search_with_context
from data_access.vector_db import RAGRetrievalPipeline

retrieval_pipeline = RAGRetrievalPipeline(...)
rag_context = await semantic_search_with_context(
    query="Python experience",
    profile_id=1,
    retrieval_pipeline=retrieval_pipeline,
)

# Process with RAG context
response = await orchestrator.process_with_rag_context(
    user_query="What is Doğan's Python experience?",
    profile_id=1,
    rag_context=rag_context,
)
```

## Direct Language/Intent Detection

```python
from orchestrator import detect_language, detect_intent, Language

# Detect language
text = "Doğan'ın Python deneyimi nedir?"
language = detect_language(text)
# Returns: Language.TURKISH

# Detect intent
intent = detect_intent(text, language)
# Returns: Intent.PROFILE_INFO
```

## RequestContext Usage

```python
from orchestrator import RequestContext, Language, Intent

# Create context manually (if needed)
context = RequestContext(
    user_query="What is Doğan's experience?",
    profile_id=1,
    language=Language.ENGLISH,
    intent=Intent.PROFILE_INFO,
    rag_context="Retrieved context here...",
)

# Convert to dict for agent consumption
context_dict = context.to_dict()
# {
#     "user_query": "What is Doğan's experience?",
#     "profile_id": 1,
#     "language": "en",
#     "intent": "profile_info",
#     "rag_context": "Retrieved context here...",
# }
```

## Agent Implementation Contract

Agents must implement the following interface:

```python
from orchestrator import RequestContext

class ProfileAgent:
    async def process(self, context: RequestContext) -> str:
        """
        Process request with language-aware context.
        
        Must:
        - Generate response in context.language
        - Use context.user_query for processing
        - Use context.profile_id for data access
        - Optionally use context.rag_context for RAG
        """
        # Detect language from context
        if context.language == Language.TURKISH:
            # Generate Turkish response
            return "Doğan'ın Python deneyimi..."
        else:
            # Generate English response
            return "Doğan has Python experience..."
```

## Error Handling

```python
try:
    response = await orchestrator.process_request(
        user_query="What is Doğan's experience?",
        profile_id=1,
    )
except ValueError as e:
    # Handle missing agent initialization
    print(f"Orchestrator not properly initialized: {e}")
except Exception as e:
    # Handle other errors
    print(f"Error processing request: {e}")
```




