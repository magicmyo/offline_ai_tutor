const API = "/chat"; // same-origin Flask endpoint
const msgs = document.getElementById("msgs");
const inp = document.getElementById("inp");
const btn = document.getElementById("send");

let SUBJECTS = ["Coding","Math","Science","English","Agent Mode"]; // fallback
fetch("/config").then(r=>r.json()).then(c=>{
  if (c.subjects && Array.isArray(c.subjects) && c.subjects.length) {
    SUBJECTS = c.subjects;
    renderTabs();
  }
});

let subject = "Coding";
let history = []; // array of [user, assistant]
function el(tag, cls, txt) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt) e.textContent = txt;
    return e;
}

function renderTabs() {
    const t = document.getElementById('tabs');
    t.innerHTML = '';
    SUBJECTS.forEach(s => {
        const b = el('button', 'tab' + (s === subject ? ' active' : ''), s);
        b.onclick = () => {
            subject = s;
            renderTabs();
        };
        t.appendChild(b);
    });
}
renderTabs();

function addMsg(text, who = "bot", toolInfo = null) {
    const msgs = document.getElementById('msgs');
    if (!msgs) return;

    const wrap = document.createElement("div");
    wrap.className = "msg-wrap " + (who === "you" ? "you" : "bot");

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = (who === "you" ? "👤" : "🤖");

    const div = document.createElement("div");
    div.className = "msg " + (who === "you" ? "you" : "bot");

    if (who === "you") {
        // user: text first, avatar after (on the right)
        wrap.appendChild(div);
        wrap.appendChild(avatar);
    } else {
        // bot: avatar first, then text (on the left)
        wrap.appendChild(avatar);
        wrap.appendChild(div);
    }


    const re = /```(\w+)?\n([\s\S]*?)```/g;
    let last = 0,
        match;

    while ((match = re.exec(text)) !== null) {
        if (match.index > last) {
            const span = document.createElement('span');
            span.textContent = text.slice(last, match.index);
            div.appendChild(span);
        }
        const lang = match[1] || "code";
        const snippet = match[2].replace(/\n+$/, '');
        const wrapper = document.createElement('div');
        wrapper.className = "code-block";
        const header = document.createElement('div');
        header.className = "code-head";
        const label = document.createElement('span');
        label.textContent = lang;
        const copyBtn = document.createElement('button');
        copyBtn.type = 'button';
        copyBtn.textContent = "Copy";
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(snippet).then(() => {
                copyBtn.textContent = "Copied!";
                setTimeout(() => copyBtn.textContent = "Copy", 1200);
            });
        });
        header.appendChild(label);
        header.appendChild(copyBtn);
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.textContent = snippet;
        pre.appendChild(code);
        wrapper.appendChild(header);
        wrapper.appendChild(pre);
        div.appendChild(wrapper);
        last = re.lastIndex;
    }
    if (last < text.length) {
        const span = document.createElement('span');
        span.textContent = text.slice(last);
        div.appendChild(span);
    }
    msgs.appendChild(wrap);

    if (toolInfo && toolInfo.name) {
        const t = document.createElement("div");
        t.className = "tool";
        t.textContent = "🛠️ Tool used: " + toolInfo.name;
        msgs.appendChild(t);
    }
    msgs.scrollTop = msgs.scrollHeight;


}

async function sendMsg() {
    const q = inp.value.trim();
    if (!q) return;
    addMsg(q, "you");
    inp.value = "";
    inp.focus();
    btn.disabled = true;

    const loaderWrap = document.createElement("div");
    loaderWrap.className = "msg-wrap bot";

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "🤖";

    const loader = document.createElement("div");
    loader.className = "msg bot";
    loader.innerHTML = `<div class="typing">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </div>`;

    loaderWrap.appendChild(avatar);
    loaderWrap.appendChild(loader);

    msgs.appendChild(loaderWrap);
    msgs.scrollTop = msgs.scrollHeight;


    msgs.scrollTop = msgs.scrollHeight;

    try {
        const r = await fetch(API, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: q,
                subject
            })
        });
        if (!r.ok) {
            const txt = await r.text().catch(() => "");
            addMsg("Error: " + (txt || r.status + " " + r.statusText), "bot");
            return;
        }
        const data = await r.json();
        if (data.error) {
            addMsg("Error: " + data.error, "bot");
            return;
        }
        addMsg(data.reply || "(no reply)", "bot",
            data.tool ? {
                name: data.tool,
                result: data.tool_result
            } : null);
    } catch (e) {
        addMsg("Network error: " + e, "bot");
    } finally {
        if (loaderWrap && loaderWrap.parentNode) loaderWrap.parentNode.removeChild(loaderWrap);
        btn.disabled = false;
    }
}

btn.addEventListener("click", sendMsg);
inp.addEventListener("keydown", e => {
    if (e.key === "Enter") sendMsg();
});

