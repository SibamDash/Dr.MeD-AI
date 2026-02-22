(function () {

    // Create floating button
    const toggleBtn = document.createElement("div");
    toggleBtn.innerHTML = "💬";
    toggleBtn.style.position = "fixed";
    toggleBtn.style.bottom = "20px";
    toggleBtn.style.right = "20px";
    toggleBtn.style.width = "60px";
    toggleBtn.style.height = "60px";
    toggleBtn.style.background = "#2563eb";
    toggleBtn.style.borderRadius = "50%";
    toggleBtn.style.display = "flex";
    toggleBtn.style.justifyContent = "center";
    toggleBtn.style.alignItems = "center";
    toggleBtn.style.color = "white";
    toggleBtn.style.fontSize = "24px";
    toggleBtn.style.cursor = "pointer";
    toggleBtn.style.boxShadow = "0 4px 12px rgba(0,0,0,0.2)";
    toggleBtn.style.zIndex = "9999";

    document.body.appendChild(toggleBtn);

    // Create chat box
    const chatBox = document.createElement("div");
    chatBox.style.position = "fixed";
    chatBox.style.bottom = "90px";
    chatBox.style.right = "20px";
    chatBox.style.width = "350px";
    chatBox.style.height = "450px";
    chatBox.style.background = "white";
    chatBox.style.borderRadius = "10px";
    chatBox.style.boxShadow = "0 8px 20px rgba(0,0,0,0.2)";
    chatBox.style.display = "none";
    chatBox.style.flexDirection = "column";
    chatBox.style.zIndex = "9999";
    chatBox.style.overflow = "hidden";

    chatBox.innerHTML = `
        <div style="background:#2563eb;color:white;padding:12px;font-weight:bold;">
            Dr.MeD Medication Assistant
        </div>
        <div id="chatMessages" style="flex:1;padding:10px;overflow-y:auto;font-size:14px;"></div>
        <div style="display:flex;border-top:1px solid #ddd;">
            <input id="chatInput" type="text" placeholder="Ask about your medicine..." 
                style="flex:1;padding:10px;border:none;outline:none;">
            <button id="chatSend" style="padding:10px 15px;border:none;background:#2563eb;color:white;cursor:pointer;">
                Send
            </button>
        </div>
    `;

    document.body.appendChild(chatBox);

    toggleBtn.onclick = () => {
        chatBox.style.display = chatBox.style.display === "flex" ? "none" : "flex";
    };

    const messagesDiv = chatBox.querySelector("#chatMessages");
    const input = chatBox.querySelector("#chatInput");
    const sendBtn = chatBox.querySelector("#chatSend");

    function addMessage(text, type) {
        const msg = document.createElement("div");
        msg.style.marginBottom = "10px";
        msg.style.padding = "8px";
        msg.style.borderRadius = "6px";
        msg.style.maxWidth = "80%";
        msg.style.whiteSpace = "pre-wrap";

        if (type === "user") {
            msg.style.background = "#dbeafe";
            msg.style.alignSelf = "flex-end";
        } else {
            msg.style.background = "#f1f5f9";
            msg.style.alignSelf = "flex-start";
        }

        msg.innerText = text;
        messagesDiv.appendChild(msg);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return msg;
    }

    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        addMessage(message, "user");
        input.value = "";

        const loading = addMessage("Typing...", "bot");

        try {
            const response = await fetch("/api/chatbot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: message,
                    context: "Medicine prescribed from uploaded medical report"
                })
            });

            const data = await response.json();
            console.log("Chatbot response:", data);
            loading.remove();

            if (data.success) {
                addMessage(data.reply, "bot");
            } else {
                addMessage("Sorry, something went wrong.", "bot");
            }

        } catch (err) {
            loading.remove();
            addMessage("Server error. Please try again.", "bot");
        }
    }

    sendBtn.onclick = sendMessage;
    input.addEventListener("keypress", function (e) {
        if (e.key === "Enter") sendMessage();
    });

})();