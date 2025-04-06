# Contextual Awareness Framework (CAF)

A modular, multi-domain pipeline built on LangGraph-style persistence and Temporal Context Awareness (TCA) for adaptive, memory-enhanced AI applications.

Supports:
- 🧠 Personalized therapist conversations
- 🔐 Security prompt monitoring and risk analysis

---

## 🗂️ Project Structure
```
contextual-awareness-framework/
├── core/               # Core logic: meaning, memory, response, pipeline
├── memory/             # Long-term memory adapters + checkpointing
├── plugins/            # Personality-specific analyzers (therapist, security)
├── examples/           # Interactive demos
├── tests/              # Unit and integration tests
├── README.md
└── requirements.txt
```

---

## 🧬 Core Components
### Core Logic (`core/`)
- `meaning_engine.py` – Interprets user intent, emotion, tone
- `pattern_tracker.py` – Detects behavioral/emotional drift
- `memory_core.py` – Session-level short-term memory
- `response_engine.py` – Crafts adaptive replies
- `pipeline.py` – Chains all components into a processing flow

### LangGraph Integration (`memory/`)
- `langgraph_adapter.py` – Persists state using LangGraph-compatible checkpoint format
- `memory_store.py` – File-based memory store
- `schemas.py` – Schema definitions for validation or structure

### Plugins (`plugins/`)
- `therapist/plugin.py` – Emotion, intent, and goal detection
- `security/plugin.py` – Prompt risk analysis and intent classification

---

## 🚀 Getting Started
### Install Requirements
```bash
pip install -r requirements.txt
```

### Run Therapist CLI Demo
```bash
python -m examples.therapist_demo
```

### Run Security CLI Demo
```bash
python -m examples.security_demo
```

---

## 📚 Use Cases
### 🧠 Therapist Mode
- Detect fatigue, anxiety, low self-worth
- Offer comfort, reflection, or motivation based on evolving state

### 🔐 Security Mode
- Detect jailbreak or unsafe prompts
- Respond with warning, denial, or neutral confirmation

---

## 🧪 Testing
To be added under the `tests/` folder. Suggested:
- Plugin unit tests
- Memory checkpoint integration tests
- Response behavior under multiple turns

---

## 💡 Inspiration
- [LangGraph long-term memory](https://blog.langchain.dev/launching-long-term-memory-support-in-langgraph/)
- [TCA paper: Multi-Turn Manipulation Defense](https://arxiv.org/abs/2503.15560)

---

## 🤝 Contributing
Want to add a new plugin (e.g. marketing assistant)? Just add a `plugins/marketing/plugin.py` and register it in `meaning_engine.py`.

PRs and feedback welcome!

