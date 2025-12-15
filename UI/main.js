document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatWindow = document.getElementById("chat-window");
  
  // Dynamically determine API URL
  const getApiUrl = () => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      // Local development
      return 'http://localhost:5000/api';
    } else {
      // Production: use relative path (Nginx proxy will route it)
      return '/api';
    }
  };
  
  const API_URL = getApiUrl();

  function appendMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    // Use textContent to prevent XSS attacks
    bubble.textContent = text;
    messageDiv.appendChild(bubble);
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const prompt = userInput.value.trim();
    if (!prompt) return;

    appendMessage(prompt, "user");
    userInput.value = "";
    userInput.disabled = true;
    appendMessage("...", "bot");

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
      
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const oldBotMsg = chatWindow.querySelector(".bot:last-child .bubble");
      
      if (!response.ok) {
        let errorMsg = "Error: Unable to get response from AI.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMsg = `Error: ${errorData.error}`;
          }
        } catch (e) {
          // Use default error message
        }
        oldBotMsg.textContent = errorMsg;
      } else {
        const data = await response.json();
        oldBotMsg.textContent = data.reply || "(No reply)";
      }
    } catch (error) {
      const oldBotMsg = chatWindow.querySelector(".bot:last-child .bubble");
      if (error.name === 'AbortError') {
        oldBotMsg.textContent = "Error: Request timed out. Please try again.";
      } else if (error instanceof TypeError) {
        oldBotMsg.textContent = "Error: Unable to connect to backend.";
      } else {
        oldBotMsg.textContent = `Error: ${error.message || "An unexpected error occurred"}`;
      }
    } finally {
      userInput.disabled = false;
      userInput.focus();
    }
  });
});