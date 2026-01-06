# Intent Detection and Routing Design

## High-Level Flow

```
User Query
    ↓
Language Detection (lightweight, deterministic)
    ↓
Intent Detection (keyword-based, extensible to LLM)
    ↓
RequestContext Creation (query + language + intent + profile_id)
    ↓
Agent Routing (based on intent)
    ↓
Agent Processing (with language context)
    ↓
Guardrail Check (always applied)
    ↓
Final Response (in detected language)
```

## Component Responsibilities

### `types.py`
- **Language Enum**: Supported languages (en, tr, extensible)
- **Intent Enum**: User intent categories
- **RequestContext**: Request-level context passed to agents
  - `user_query`: Original text
  - `profile_id`: Profile identifier
  - `language`: Detected language
  - `intent`: Detected intent
  - `rag_context`: Optional RAG context

### `language_detector.py`
- **LanguageDetector**: Lightweight, deterministic language detection
  - Character-based heuristics (Turkish-specific chars)
  - Keyword-based detection (common Turkish words)
  - Defaults to English
  - Executed **before** intent detection

### `intent_detector.py`
- **IntentDetector**: Intent classification
  - Keyword-based matching (primary)
  - Extensible to LLM-based classification (future)
  - Returns single dominant intent
  - Uses detected language for language-specific patterns

### `orchestrator.py`
- **Orchestrator**: Central routing component
  - Receives user query + profile_id
  - Orchestrates language + intent detection
  - Routes to appropriate agent
  - Applies guardrail check
  - Returns response in detected language

## Intent Routing Map

| Intent | Agent | Use Case |
|--------|-------|----------|
| `PROFILE_INFO` | `ProfileAgent` | Skills, experience, background questions |
| `GITHUB_INFO` | `GitHubAgent` | Projects, repositories, code-related |
| `CV_REQUEST` | `CVAgent` | CV download/generation requests |
| `GENERAL_QUESTION` | `ProfileAgent` | Vision, interests, career goals |
| `OUT_OF_SCOPE` | `GuardrailAgent` | Irrelevant or unsupported queries |

## Language Detection Strategy

### Turkish Detection
- **Character-based**: Detects Turkish-specific characters (ç, ğ, ı, ö, ş, ü)
- **Keyword-based**: Matches common Turkish words
- **Heuristic**: If Turkish chars OR 2+ Turkish keywords → Turkish

### English Detection
- **Default**: Falls back to English if no Turkish indicators
- **Mixed content**: If mostly English with some Turkish chars → Turkish

### Extensibility
- Add new language to `Language` enum
- Extend `LanguageDetector` with language-specific heuristics
- No changes needed to agents (they receive language as context)

## Agent Contract

All agents must implement:
```python
async def process(self, context: RequestContext) -> str:
    """
    Process request with language-aware context.
    
    Must:
    - Generate response in context.language
    - Use context.user_query for processing
    - Use context.profile_id for data access
    - Optionally use context.rag_context for RAG
    """
    pass
```

Agents receive:
- `context.user_query`: Original user text
- `context.profile_id`: Profile identifier
- `context.language`: Detected language (Language enum)
- `context.intent`: Detected intent (Intent enum)
- `context.rag_context`: Optional pre-retrieved RAG context

Agents must:
- **Never override detected language**
- Generate responses strictly in `context.language`
- Translate retrieved context if necessary
- Use tools for data access (not direct DB access)

## Examples

### Example 1: Turkish Input → Turkish Output
```
Input: "Doğan'ın Python deneyimi nedir?"
  ↓
Language Detection: Turkish (detected via "deneyimi", "nedir")
  ↓
Intent Detection: PROFILE_INFO (detected via "deneyimi")
  ↓
Routing: ProfileAgent
  ↓
Agent Response: "Doğan'ın Python konusunda 5 yıllık deneyimi var..."
  ↓
Output: "Doğan'ın Python konusunda 5 yıllık deneyimi var..."
```

### Example 2: English Input → English Output
```
Input: "What is Doğan's experience with Python?"
  ↓
Language Detection: English (no Turkish indicators)
  ↓
Intent Detection: PROFILE_INFO (detected via "experience")
  ↓
Routing: ProfileAgent
  ↓
Agent Response: "Doğan has 5 years of experience with Python..."
  ↓
Output: "Doğan has 5 years of experience with Python..."
```

### Example 3: Mixed-Language Input
```
Input: "Doğan'ın GitHub projects hakkında bilgi ver"
  ↓
Language Detection: Turkish (detected via "Doğan'ın", "hakkında", "bilgi")
  ↓
Intent Detection: GITHUB_INFO (detected via "GitHub", "projects")
  ↓
Routing: GitHubAgent
  ↓
Agent Response: "Doğan'ın GitHub'da birkaç projesi var..."
  ↓
Output: "Doğan'ın GitHub'da birkaç projesi var..."
```

### Example 4: CV Request
```
Input: "CV'yi indirmek istiyorum"
  ↓
Language Detection: Turkish (detected via "CV'yi", "istiyorum")
  ↓
Intent Detection: CV_REQUEST (detected via "CV", "indirmek")
  ↓
Routing: CVAgent
  ↓
Agent Response: "CV dosyanız hazırlanıyor..."
  ↓
Output: "CV dosyanız hazırlanıyor..."
```

### Example 5: Out-of-Scope
```
Input: "What's the weather today?"
  ↓
Language Detection: English
  ↓
Intent Detection: OUT_OF_SCOPE (detected via "weather")
  ↓
Routing: GuardrailAgent
  ↓
Agent Response: "I can only answer questions about the candidate's profile..."
  ↓
Output: "I can only answer questions about the candidate's profile..."
```

## Design Decisions

1. **Language Detection First**: Language is detected before intent to enable language-specific intent patterns
2. **Deterministic Detection**: Character/keyword-based detection is fast and deterministic (no LLM calls)
3. **Extensible Intents**: Intent enum can be extended; routing logic updated accordingly
4. **Context Object**: RequestContext ensures language/intent are passed consistently to agents
5. **Guardrail Always Applied**: All responses go through guardrail check before returning
6. **No Language Override**: Agents cannot override detected language; must respond in context.language
7. **Tool-Based RAG**: RAG context is retrieved via tools, not directly by orchestrator

## Future Enhancements

1. **LLM-Based Intent Detection**: For ambiguous queries, use LLM classification
2. **Multi-Language Support**: Add Spanish, German, etc. to Language enum
3. **Confidence Scores**: Return confidence scores for language/intent detection
4. **Intent Disambiguation**: Use LLM to disambiguate between similar intents
5. **Language-Specific Intent Patterns**: Train language-specific keyword sets




