document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("user-input");
  const chatWindow = document.getElementById("chat-window");

  const API_BASE_URL = window.API_BASE_URL || "/api";

  function addMessage(text, sender) {
    const div = document.createElement("div");
    div.classList.add("message", sender);
    div.textContent = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return div;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const prompt = input.value.trim();
    if (!prompt) return;

    addMessage(prompt, "user");
    input.value = "";

    const botDiv = addMessage("", "bot");

    try {
      const res = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt })
      });

      if (!res.ok || !res.body) {
        throw new Error("Streaming failed");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        chunk.split("\n\n").forEach(line => {
          if (!line.startsWith("data: ")) return;

          const data = line.replace("data: ", "");

          if (data === "[DONE]") return;
          if (data === "[ERROR]") {
            botDiv.textContent += "\n⚠️ Error generating response.";
            return;
          }

          botDiv.textContent += data;
          chatWindow.scrollTop = chatWindow.scrollHeight;
        });
      }

    } catch (err) {
      console.error(err);
      botDiv.textContent = "AI service unavailable";
    }
  });
});
