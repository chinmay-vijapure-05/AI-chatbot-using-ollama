document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatWindow = document.getElementById("chat-window"); // Function to append message to chat window
  const API_URL = "/api";
  function appendMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.textContent = text;
    messageDiv.appendChild(bubble);
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  } // Handle form submit
  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const prompt = userInput.value.trim();
    if (!prompt) return;
    appendMessage(prompt, "user");
    userInput.value = "";
    userInput.disabled = true;
    // Show loading response
    appendMessage("...", "bot");
    try {
      // Replace with your backend API URL
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const oldBotMsg = chatWindow.querySelector(".bot:last-child .bubble");
      if (!response.ok) {
        oldBotMsg.textContent = "Error: Unable to get response from AI.";
      } else {
        const data = await response.json(); // Remove loading placeholder before showing actual response
        oldBotMsg.textContent = data.reply || "(No reply)";
      }
    } catch (error) {
      const oldBotMsg = chatWindow.querySelector(".bot:last-child .bubble");
      oldBotMsg.textContent = "Error: Unable to connect to backend.";
    } finally {
      userInput.disabled = false;
      userInput.focus();
    }
  });
});
