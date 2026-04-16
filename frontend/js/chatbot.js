// chatbot.js — floating AI chat widget (injected on all pages)

document.addEventListener("DOMContentLoaded", () => {
    // Inject HTML
    document.body.insertAdjacentHTML("beforeend", `
    <div id="chatbot-bubble">
      <button id="chat-toggle-btn" title="Ask CloudBot">&#129302;</button>
      <div id="chat-window">
        <div id="chat-header">
          <div class="d-flex align-items-center gap-2">
            <span>&#129302;</span>
            <div>
              <div style="font-size:0.95rem;">CloudBot</div>
              <div style="font-size:0.7rem;opacity:0.8;">Powered by Llama 3</div>
            </div>
          </div>
          <div class="d-flex gap-2 align-items-center">
            <button onclick="clearChatHistory()" title="Clear history"
              style="background:rgba(255,255,255,0.2);border:none;color:#fff;border-radius:6px;padding:2px 8px;font-size:0.75rem;cursor:pointer;">
              Clear
            </button>
            <button onclick="toggleChat()" style="background:none;border:none;color:#fff;font-size:1.2rem;cursor:pointer;line-height:1;">&#10005;</button>
          </div>
        </div>
        <div id="chat-messages">
          <div class="msg-ai">
            Hi! I'm CloudBot 👋 Ask me anything about your cloud resources, costs, or DBMS concepts.
          </div>
        </div>
        <div id="chat-input-area">
          <input id="chat-input" type="text" placeholder="Ask something..." autocomplete="off" />
          <button id="chat-send-btn" onclick="sendChatMessage()">&#10148;</button>
        </div>
      </div>
    </div>`);

    document.getElementById("chat-toggle-btn").addEventListener("click", toggleChat);
    document.getElementById("chat-input").addEventListener("keydown", e => {
        if (e.key === "Enter") sendChatMessage();
    });

    loadChatHistory();
});

function toggleChat() {
    const win = document.getElementById("chat-window");
    win.classList.toggle("open");
}

async function loadChatHistory() {
    try {
        const rows = await apiGet("/ai/chat/history");
        const msgs = document.getElementById("chat-messages");
        // Keep the welcome message, append history
        rows.slice(-10).forEach(row => {
            appendMsg("user", row.user_question);
            appendMsg("ai", row.ai_response);
        });
    } catch (_) {}
}

async function clearChatHistory() {
    try {
        await apiDelete("/ai/chat/history");
        const msgs = document.getElementById("chat-messages");
        msgs.innerHTML = '<div class="msg-ai">Chat history cleared. How can I help you?</div>';
    } catch (e) {
        showToast("Could not clear history: " + e.message, "error");
    }
}

async function sendChatMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";

    appendMsg("user", message);
    const typingId = appendMsg("ai-typing", "CloudBot is thinking...");

    try {
        const data = await apiPost("/ai/chat", { message });
        removeMsg(typingId);
        appendMsg("ai", data.response);
    } catch (e) {
        removeMsg(typingId);
        appendMsg("ai", "Sorry, I couldn't connect to the AI. Check that the backend is running and your Groq API key is set.");
    }
}

let msgCounter = 0;
function appendMsg(type, text) {
    const msgs = document.getElementById("chat-messages");
    const id = "msg-" + (++msgCounter);
    const cls = type === "user" ? "msg-user" : type === "ai-typing" ? "msg-typing" : "msg-ai";
    msgs.insertAdjacentHTML("beforeend", `<div id="${id}" class="${cls}">${escapeHtml(text)}</div>`);
    msgs.scrollTop = msgs.scrollHeight;
    return id;
}

function removeMsg(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
}
