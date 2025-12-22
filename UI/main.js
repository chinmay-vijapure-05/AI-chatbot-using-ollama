document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("user-input");
  const chatWindow = document.getElementById("chat-window");

  /**
   * API base URL
   * - Local dev: http://localhost:5000/api
   * - Deployed: https://your-backend.onrender.com/api
   */
  const API_BASE_URL = window.API_BASE_URL || "/api";

  function addMessage(text, sender) {
    const div = document.createElement("div");
    div.classList.add("message", sender);
    div.textContent = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const prompt = input.value.trim();
    if (!prompt) return;

    addMessage(prompt, "user");
    input.value = "";

    const typing = document.createElement("div");
    typing.classList.add("message", "bot");
    typing.textContent = "Thinking...";
    chatWindow.appendChild(typing);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      typing.textContent = data.reply || "No response from AI";

    } catch (err) {
      console.error(err);
      typing.textContent = "AI service unavailable";
    }
  });
});
