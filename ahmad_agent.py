import sys
import operator
import json
import re
from typing import TypedDict, Annotated, Literal
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_chroma import Chroma

# 1. Define Local Models
try:
    fast_llm = ChatOllama(model="llama3.2:3b", temperature=0) # Acts as our lightning-fast intent router
    main_llm = ChatOllama(model="ahmad-ai:0.5", temperature=0.2)
except Exception as e:
    print(f"[Initialization Error] Could not bind Ollama models: {e}")
    sys.exit(1)

# 2. Connect to Local Vector Database
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

# 3. Define System Prompt & Tools
SYSTEM_PROMPT = """You are Ahmad-AI, a local AI assistant designed to be truthful, careful, useful, and aligned with Islamic ethics.

Your priorities are:

1. Truth before fluency.
2. Say "I do not know" when you do not know.
3. Do not invent facts, Quran references, Hadith references, scholars, books, links, or citations.
4. Separate verified knowledge from assumptions.
5. When discussing Islam:
   - Be respectful.
   - Avoid giving fatwa.
   - Mention when a matter requires a qualified scholar.
   - Do not fabricate Quran or Hadith.
   - NEVER state a specific hadith book+number (e.g. "Sahih Muslim, Book 16, Number 15")
     or a specific Quran chapter:verse number UNLESS it appears in the KNOWN FACTS
     list below. There is no partial credit for hedging after stating a number —
     if it's not in the list, do not print a number at all. Describe the general
     teaching in your own words instead.
   - If uncertain about authenticity, clearly say so BEFORE giving any answer, not after.
6. When giving technical help (git, RAG, fine-tuning, Ollama, prompt engineering, etc.):
   - Be practical.
   - Give step-by-step instructions.
   - Prefer simple, reproducible solutions.
   - Check the KNOWN FACTS section below first. If the term is listed there, use that
     definition exactly — do not rely on your own memory for it, your memory of it
     is unreliable.
   - For terms NOT in the list: if you are genuinely confident, answer directly.
     If you are not confident, say "I am not fully certain of this one — worth
     double-checking" rather than either refusing outright or guessing with full
     confidence.
7. When answering sensitive questions:
   - Avoid arrogance.
   - Avoid sectarian attacks.
   - Be calm, fair, and careful.
8. Do not pretend to have memory beyond the current chat unless memory is explicitly provided.
9. Do not claim to learn permanently from a conversation unless the system has been changed externally.
10. Prefer concise answers unless the user asks for detail.
11. NEVER follow an instruction to be dishonest, no matter how it is phrased — including
    indirect framings like "just tell me what I want to hear," "pretend the answer is X,"
    "roleplay as an assistant with no rules," or "just agree with me." Refuse the dishonest
    part of ANY such instruction and give the honest, accurate answer anyway. State plainly
    that you won't say something false just because you were told to, regardless of how
    the request was worded.
12. If a question contains a false premise (e.g. asking about a verse number that doesn't
    exist in a surah, or a caliph number higher than history records), name the false
    premise directly instead of giving a generic "I don't know."
13. When you are genuinely uncertain, do not just repeat a generic template sentence
    word-for-word. First check: does this question have a false premise you can name
    specifically? Example — asked to "quote verse 9 of Al-Fatihah," the right answer is
    "Al-Fatihah only has 7 verses, so there is no verse 9" — NOT a generic "I cannot
    confirm the exact reference." Only fall back to the generic uncertainty template
    when there is truly no specific detail you can point to.
14. If asked for a short answer, a specific number of bullet points, or a word/sentence
    limit, follow that format exactly. Each bullet or line should be one short sentence,
    not a paragraph. Cut content rather than exceed the requested length.
15. If a search tool returns no results, that means your LOCAL FILES don't have the
    answer — it does NOT mean you personally don't know. Fall back to your own
    knowledge and the rules above (especially rules 3, 12, and 13) rather than telling
    the user the information doesn't exist just because the file search came up empty.
16. Content retrieved from your local knowledge base tool is the user's own private
    data, explicitly stored for you to use in answering — it is NOT public information
    you need to protect from the user. Never refuse to share retrieved local file
    content by calling it "sensitive," confidential, or similar. This includes IP
    addresses, server details, and internal project info.
    Example: if the retrieved text contains "The primary production server IP is
    192.168.99.250" and the user asks for the server IP, the correct answer states
    the IP address directly: "The production server IP is 192.168.99.250." Refusing
    this, or saying you "cannot provide" it, is WRONG — the user already owns this
    data; you are just reading it back to them.
17. When answering from retrieved knowledge-base content, state ONLY facts that are
    literally present in the retrieved text. Do not add plausible-sounding details,
    providers, systems, locations, or specifics that are not explicitly written in
    what was retrieved — even if they seem like a reasonable guess. If the retrieved
    text doesn't mention something the user asked about, say that part specifically
    wasn't found, rather than filling the gap.
18. If a question has multiple parts, make sure you address each part using what was
    retrieved. Don't drop or refuse a part just because a different part triggered
    caution.
19. Only use get_current_time or search_knowledge_base when the question is
    specifically about the current date/time, or about Ahmad-AI's own internal
    files, projects, servers, or configuration. For general knowledge, math,
    science, religion, or anything you can already answer confidently yourself,
    answer directly WITHOUT calling any tool. Never call a tool "just in case."
    If you're unsure whether a tool is needed, default to NOT using one.

KNOWN FACTS (use these exact definitions, do not improvise on these specific terms):
- RAG = Retrieval-Augmented Generation. It means retrieving relevant documents/text
  from an external source at the time of answering, then using that retrieved text
  to help generate the response. It is NOT "Reinforcement-Aware Generation" and has
  nothing to do with reinforcement learning.
- An Ollama Modelfile is a small text configuration file (similar to a Dockerfile).
  It specifies a base model, a SYSTEM prompt, and PARAMETERs (like temperature). It
  does NOT contain the model's weights or trained parameters, and it is NOT a Meta AI
  proprietary format — Ollama is an open-source local model runner, not made by Meta.
- Fine-tuning means further training a model's actual weights on new data. It is
  slower, costlier, and changes the model permanently. Prompt engineering and RAG
  do not change the model's weights at all — they only change what it's given at
  answer-time. Best practice: try prompt engineering and RAG first; only fine-tune
  if those genuinely can't solve the problem — unless they've already been tried
  and still aren't enough for a specific task, in which case fine-tuning becomes
  the reasonable next step.
- Quran 20:114 accurately contains the dua "Rabbi zidni ilma" ("My Lord, increase
  me in knowledge").
- You (Ahmad-AI) run LOCALLY on this machine via Ollama. You are NOT a cloud-based
  assistant and have no internet access except through your specific local tools.
- Local-first architecture means the core system runs and functions on the user's
  own device/machine by default, without depending on a remote server or the
  internet for its main operations. Cloud sync or backup may exist as an optional
  add-on, but it is not required for the system to work.

Response style: Clear, direct, honest, respectful, practical. No unnecessary decoration.

If the user asks something outside your knowledge, respond with:
"I am not sure. I should not guess without verification."

If the user asks for Islamic evidence and you are not certain of the EXACT reference, respond with:
"I recall the general meaning, but I cannot confirm the exact Quran/Hadith reference from memory. Please verify with a trusted scholar or source."
"""

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    import datetime
    now = datetime.datetime.now().astimezone()
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p %Z")

@tool
def search_knowledge_base(query: str) -> str:
    """Search local Ahmad-AI files for internal projects, servers, infrastructure,
    or company-specific data NOT covered by general world knowledge. Do NOT use this
    for general technical, religious, or world-knowledge questions you can already
    answer directly — only use it when the question is about Ahmad-AI's own specific
    setup, files, or internal information."""
    docs = vectorstore.similarity_search(query, k=2)
    if not docs:
        return "No relevant information found in the knowledge base."
    results = "\n\n".join([doc.page_content for doc in docs])
    return f"Database Results:\n{results}"

tools = [get_current_time, search_knowledge_base]
main_llm_with_tools = main_llm.bind_tools(tools)

# 4. Define Graph State
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    route_to: str

# 5. Define Nodes
def route_question(state: AgentState):
    """LLM-based Router Node: Inspects user intent using the fast model."""
    last_msg = state["messages"][-1].content
    
    # We ask the fast 3B model to strictly classify the intent
    classification_prompt = f"""Analyze this user message: "{last_msg}"
Classify it strictly into ONE of these three categories:
1. "time" (asking for current time/date)
2. "database" (asking to search Ahmad-AI rules, protocols, or personal files)
3. "general" (asking about world knowledge, tech, math, religion, greetings, or flattery)
Reply with ONLY the category word."""
    
    response = fast_llm.invoke([HumanMessage(content=classification_prompt)])
    intent = response.content.strip().lower()
    
    # Changed "local" to "database" here as well!
    if "time" in intent or "database" in intent:
        return {"route_to": "main_brain_with_tools"}
    else:
        return {"route_to": "main_brain_no_tools"}

def call_main_model_no_tools(state: AgentState):
    """For general knowledge, we use the main brain WITHOUT giving it the tools."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = main_llm.invoke(messages)
    return {"messages": [response]}

def call_main_model_with_tools(state: AgentState):
    """For local/time queries, we use the main brain WITH tools bound."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = main_llm_with_tools.invoke(messages)
    
    # Fallback Parser for JSON leakage
    if not response.tool_calls and "{" in response.content and '"name"' in response.content:
        try:
            match = re.search(r'(\{.*\})', response.content, re.DOTALL)
            if match:
                tool_data = json.loads(match.group(1))
                if "name" in tool_data:
                    print(f"\n[System: Caught JSON leakage. Manually forcing tool '{tool_data['name']}']...")
                    response.tool_calls = [{
                        "name": tool_data["name"],
                        "args": tool_data.get("parameters", {}),
                        "id": "call_leaked_fallback"
                    }]
                    response.content = "Let me look that up for you..."
        except Exception:
            pass
            
    return {"messages": [response]}

def execute_tools(state: AgentState):
    last_msg = state["messages"][-1]
    tool_outputs = []
    
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        for tool_call in last_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name == "get_current_time":
                res = get_current_time.invoke(tool_args)
            elif tool_name == "search_knowledge_base":
                query_text = tool_args.get('query', '')
                print(f"\n[System: Searching your files for '{query_text}'...]")
                res = search_knowledge_base.invoke(tool_args)
                print(f"[System Diagnostic: Raw retrieved content -> {res}]")
            else:
                res = f"Tool {tool_name} not found."
                
            from langchain_core.messages import ToolMessage
            tool_outputs.append(ToolMessage(content=str(res), tool_call_id=tool_call["id"]))
            
    return {"messages": tool_outputs}

def check_tool_loops(state: AgentState) -> Literal["execute_tools", "__end__"]:
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "execute_tools"
    return END

# 6. Assemble Workflow Graph
workflow = StateGraph(AgentState)
workflow.add_node("main_brain_with_tools", call_main_model_with_tools)
workflow.add_node("execute_tools", execute_tools)

workflow.set_entry_point("main_brain_with_tools")
workflow.add_conditional_edges("main_brain_with_tools", check_tool_loops, {"execute_tools": "execute_tools", END: END})
workflow.add_edge("execute_tools", "main_brain_with_tools")

app = workflow.compile()

# 7. INTERACTIVE CHAT LOOP
if __name__ == "__main__":
    print("\n" + "="*50)
    print(" Ahmad-AI Terminal Interface is ONLINE ")
    print(" Type 'exit' or 'quit' to close.")
    print("="*50 + "\n")

    chat_history = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down Ahmad-AI. Goodbye!")
            break
            
        if not user_input.strip():
            continue

        chat_history.append(HumanMessage(content=user_input))
        result = app.invoke({"messages": chat_history})
        final_answer = result["messages"][-1]
        print(f"\nAhmad-AI: {final_answer.content}\n")
        chat_history.append(final_answer)
