import os, re, json, glob, requests
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, send_from_directory, make_response
from pypdf import PdfReader

CONFIG_PATH = os.environ.get("WEB_CONFIG", "./config.json")
_CONFIG_MTIME = None

# defaults (fallbacks if config.json is missing)
DEFAULT_SYSTEM = """
You are an offline AI tutoring AGENT. You can either answer normally,
or call ONE tool when useful. To call a tool, output EXACTLY one line:
<tool_call>{"name":"TOOL_NAME","arguments":{...}}</tool_call>

Available tools:
1) calculator(expression: str) #calculates numeric operations
2) search_notes(query: str) # searches local ./notes. output should return file name also

MANDATORY: If the user's message is a math expression containing only
digits, spaces, and + - * / ( ), you MUST call the calculator tool with
the exact expression. Do NOT compute it yourself. Output only the
<tool_call> line and nothing else.

RULES:
- If the user's message CONTAINS any arithmetic expression (digits and + - * / ( )),
  EXTRACT the expression (e.g., "8/2", "(2+3)*4") and call the calculator with it.
  Do NOT compute yourself. Output only the <tool_call>.
- Use search_notes only when the user asks to find/read notes or mentions chapters/pages
  without a solvable expression.

Examples:
User: "Simplify 8/2 from Chapter 3 fractions" 
<tool_call>{"name":"calculator","arguments":{"expression":"8/2"}}</tool_call>

User: "Find Chapter 3 fractions"
<tool_call>{"name":"search_notes","arguments":{"query":"Chapter 3 fractions"}}</tool_call>

After the tool returns, write a clear final answer using the tool result.
Keep outputs concise in less than 100 words and helpful for students.
"""

# behaviour by Subjects
DEFAULT_SUBJECT_PRIMERS = {
    "Coding":  "You are tutoring Coding. Answer in under 100 words. Prefer step-by-step explanation with tiny examples (≤15 lines).",
    "Math":    "You are tutoring Math. Answer in under 100 words. Use concrete objects. Keep reasoning short.",
    "Science": "You are tutoring Science. Answer in under 100 words. Use everyday phenomena.",
    "English": "You are tutoring English. Answer in under 100 words. Teach with short examples, then give one tiny practice.",

}


def _apply_config(conf: dict):
    global API_URL, MODEL, TIMEOUT, SYSTEM, SUBJECT_PRIMERS, WEB_PORT
    API_URL = conf.get("api_url", os.environ.get("LLAMA_URL", "http://127.0.0.1:8081/v1/chat/completions"))
    MODEL   = conf.get("model",   os.environ.get("LLAMA_MODEL", "local-model"))
    TIMEOUT = int(conf.get("timeout", 120))
    SYSTEM  = conf.get("system", DEFAULT_SYSTEM)
    WEB_PORT = int(conf.get("web_port", 8000))
    SUBJECT_PRIMERS = conf.get("subject_primers", DEFAULT_SUBJECT_PRIMERS)

def _load_config_file() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def maybe_reload_config():
    """Reload config.json when it changes (cheap, called per request)."""
    global _CONFIG_MTIME
    try:
        m = os.path.getmtime(CONFIG_PATH)
        if _CONFIG_MTIME != m:
            _apply_config(_load_config_file())
            _CONFIG_MTIME = m
    except Exception:
        if _CONFIG_MTIME is None:
            # first run and no file — still apply defaults
            _apply_config({})
            _CONFIG_MTIME = 0

# initial load
maybe_reload_config()

# Tools
def calculator(expression: str) -> str:

    try:
        if not re.fullmatch(r"[\d()+\-*/.\s]+", expression):
            return "Blocked: only numbers and + - * / ( ) allowed."
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Calculator error: {e}"

def search_notes(query: str, base_dir: str = "./notes") -> str:
    os.makedirs(base_dir, exist_ok=True)
    hits = []
    for path in glob.glob(os.path.join(base_dir, "**", "*.*"), recursive=True):
        low = path.lower()
        if low.endswith((".txt", ".md")):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                if query.lower() in text.lower():
                    i = text.lower().find(query.lower())
                    s = max(0, i - 120); e = min(len(text), i + 120)
                    hits.append({"file": path, "snippet": text[s:e].replace("\n"," ")})
            except:
                pass
        elif low.endswith(".pdf"):
            try:
                pdf = PdfReader(path)
                first_pages = "\n".join([(p.extract_text() or "") for p in pdf.pages[:3]])
                if query.lower() in first_pages.lower():
                    i = first_pages.lower().find(query.lower())
                    s = max(0, i - 120); e = min(len(first_pages), i + 120)
                    hits.append({"file": path, "snippet": first_pages[s:e].replace("\n"," ")})
            except:
                pass
    if not hits:
        return "No matches."
    return "\n".join([f"- {h['file']}: {h['snippet']}" for h in hits[:8]])

TOOLS = {
    "calculator": {
        "fn": calculator,
        "schema": {"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"]}
    },
    "search_notes": {
        "fn": search_notes,
        "schema": {"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}
    }
}




def build_agent_prompt(user_text: str) -> List[Dict[str,str]]:
    """Agent mode: pure SYSTEM rules, no tutoring primer."""
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_text}
    ]


def llm(messages: List[Dict[str,str]]) -> str:
    payload = {"model": MODEL, "messages": messages, "temperature": 0.2, "max_tokens": 200, "stream": False}
    r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

TOOL_RE = re.compile(r"<tool_call>\s*(\{.*?})\s*</tool_call>", re.DOTALL)

def extract_tool_json(text: str) -> Optional[str]:
    # try strict match first
    m = TOOL_RE.search(text)
    if m:
        return m.group(1)

    # fallback: handle missing </tool_call>; scan balanced braces
    i = text.find("<tool_call>")
    if i == -1:
        return None
    j = text.find("{", i)
    if j == -1:
        return None
    depth = 0
    for k, ch in enumerate(text[j:], start=j):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[j:k+1]
    return None

def agent_answer(user_text: str, subject: Optional[str] = None) -> Dict[str, Optional[str]]:
    maybe_reload_config()

    if subject == "Agent Mode":
        messages = build_agent_prompt(user_text)
    else:
        subj_sysprompt = SUBJECT_PRIMERS.get(subject, "")
        sysprompt = subj_sysprompt
        messages = [{"role": "system", "content": sysprompt}, {"role": "user", "content": user_text}]

    out = llm(messages)

    spec_text = extract_tool_json(out.strip())
    if not spec_text:
        return {"reply": out, "tool": None, "tool_result": None}

    tool = None; tool_result = None
    try:
        #spec = json.loads(m.group(1))
        spec = json.loads(spec_text)
        name = spec.get("name", "")
        args = spec.get("arguments", {})
        tool = name
        if name not in TOOLS:
            final = f"I attempted to use an unavailable tool '{name}'."
        else:
            fn = TOOLS[name]["fn"]
            tool_result = fn(**args)
            # feed tool result + subject primer again so the final answer stays on style
            messages.append({"role": "assistant", "content": out})
            messages.append({"role": "system", "content": f"Tool '{name}' returned:\n{tool_result}"})
            if subject and subject in SUBJECT_PRIMERS:
                messages.append({"role": "system", "content": SUBJECT_PRIMERS[subject]})
            final = llm(messages)
        return {"reply": final, "tool": tool, "tool_result": tool_result}
    except Exception as e:
        return {"reply": f"I tried to call a tool but failed: {e}", "tool": tool, "tool_result": tool_result}

# Flask app (serves API + index.html)
app = Flask(__name__, static_folder=".", static_url_path="")

def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return resp

@app.route("/", methods=["GET"])
def root():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return _cors(make_response())
    data = request.get_json(force=True, silent=True) or {}
    msg = (data.get("message") or "").strip()
    subject = (data.get("subject") or "").strip()
    if not msg:
        return _cors(jsonify({"error": "Empty message"})), 400
    result = agent_answer(msg, subject=subject or None)
    return _cors(jsonify(result))

@app.route("/config", methods=["GET"])
def get_config():
    maybe_reload_config()
    data = {
        "api_url": API_URL,
        "model": MODEL,
        "timeout": TIMEOUT,
        "subject_primers": SUBJECT_PRIMERS,
        "subjects": list(SUBJECT_PRIMERS.keys()) + ["Agent Mode"]
    }
    return _cors(jsonify(data))

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(".", "images/favicon.ico", mimetype="image/x-icon")

if __name__ == "__main__":
    port = WEB_PORT #int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
