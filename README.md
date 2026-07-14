# Ahmad-AI: Fully Local, Privacy-First Agentic RAG System

Ahmad-AI is a production-grade, entirely offline AI Assistant built to query internal systems and documentation securely. By running Llama 3.1 (8B) locally via Ollama, utilizing LangGraph for stateful workflow orchestration, and ChromaDB for vector retrieval, Ahmad-AI ensures 100% data sovereignty with zero external API dependencies.

## 🚀 Key Features

*   **Stateful Agentic Workflows:** Developed with **LangGraph** to manage conversational history and tool-calling transitions robustly.
*   **Safety Alignment Override:** Implements custom prompt-engineering heuristics to bypass default LLM RLHF refusals, allowing secure retrieval of sensitive local system data (like internal IP addresses) without deflections or hallucinations.
*   **Semantic Routing Layer (v0.6):** Integrates a local embedding-based classifier to route traffic before hitting the LLM. It distinguishes between general knowledge queries (which bypass tools) and private system queries (which trigger the vector database), drastically reducing CPU latency and eliminating schema over-triggering.
*   **Offline Vector RAG:** Utilizes **ChromaDB** and local embeddings (`nomic-embed-text`) to perform semantic search over proprietary files.



## 🛠️ Architecture

               ┌───────────────────────┐
               │   User Input Prompt   │
               └───────────┬───────────┘
                           │
                           ▼
             ┌───────────────────────────┐
             │  Semantic Routing Node    │ (Ollama Embeddings / Cosine Similarity)
             └─────────────┬─────────────┘
                           ├──────────────────────────────┐
             [Private System Query]                 [General Query]
                           │                              │
                           ▼                              ▼
             ┌───────────────────────────┐  ┌───────────────────────────┐
             │   RAG Brain (With Tools)  │  │   Conversational Brain    │ (No tools bound)
             └─────────────┬─────────────┘  └─────────────┬─────────────┘
                           │                              │
                           ▼                              ▼
             ┌───────────────────────────┐                │
             │ ChromaDB / System Search  │                │
             └─────────────┬─────────────┘                │
                           └──────────────┬───────────────┘
                                          ▼
                             ┌─────────────────────────┐
                             │     Final Response      │
                             └─────────────────────────┘


## 💻 Tech Stack

* **Orchestration:** LangGraph
* **LLM Engine:** Ollama (Llama 3.1 8B)
* **Embeddings:** `nomic-embed-text`
* **Vector Database:** ChromaDB
* **Frameworks:** Python, LangChain, LangChain-Ollama

### 1. Prerequisites
Ensure you have Python 3.10+ and [Ollama](https://ollama.com/) installed on your machine.

### 2. Pull Local Models
ollama pull llama3.1
ollama pull nomic-embed-text

### 3. Installation
Clone the repository and install the dependencies:

git clone [https://github.com/emadaed/Ahmad-AI.git](https://github.com/emadaed/Ahmad-AI.git)
cd Ahmad-AI
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

### 4. Running the Agent
Run the interactive terminal interface:
python ahmad_agent.py

## ⚠️ Known Quirks & Optimization Notes

* **Schema Over-Triggering (v0.5):** In earlier iterations where tools were globally bound to a single LLM node, the 8B model suffered from subtle JSON leakage—often triggering tool calls for general AI terms (e.g., "quantization") due to semantic proximity to the system prompts.
* **The Fix (v0.6):** This bottleneck is fully mitigated in the current branch by decoupling the conversational node from the tool node and utilizing the pre-LLM mathematical routing layer.
