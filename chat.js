document.addEventListener("DOMContentLoaded", function () {
    // DOM elements
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatLog = document.getElementById("chat-log");
    const sendButton = document.getElementById("send-button");
    const errorMessage = document.getElementById("error-message");
    const typingIndicator = document.getElementById("typing-indicator");
    const charCount = document.getElementById("char-count");
    const welcomeTime = document.getElementById("welcome-time");

    // Initialize
    init();

    function init() {
        // Set welcome message time
        welcomeTime.textContent = getCurrentTime();
        
        // Focus on input
        chatInput.focus();
        
        // Setup event listeners
        setupEventListeners();
        
        // Auto-resize textarea
        autoResizeTextarea();
    }

    function setupEventListeners() {
        // Form submission
        chatForm.addEventListener("submit", handleFormSubmit);
        
        // Input events
        chatInput.addEventListener("input", handleInputChange);
        chatInput.addEventListener("keydown", handleKeyDown);
        
        // Button state management
        chatInput.addEventListener("input", updateSendButton);
    }

    function handleFormSubmit(e) {
        e.preventDefault();
        sendMessage();
    }

    function handleInputChange() {
        updateCharCount();
        autoResizeTextarea();
    }

    function handleKeyDown(e) {
        // Send on Enter (without Shift)
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    function updateCharCount() {
        const currentLength = chatInput.value.length;
        charCount.textContent = `${currentLength}/1000`;
        
        // Change color based on character count
        if (currentLength > 900) {
            charCount.style.color = "#dc3545";
        } else if (currentLength > 800) {
            charCount.style.color = "#fd7e14";
        } else {
            charCount.style.color = "#6c757d";
        }
    }

    function updateSendButton() {
        const hasText = chatInput.value.trim().length > 0;
        sendButton.disabled = !hasText;
        sendButton.style.opacity = hasText ? "1" : "0.6";
    }

    function autoResizeTextarea() {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    }

    async function sendMessage() {
        const userMessage = chatInput.value.trim();
        
        if (!userMessage) {
            showError("Please enter a message");
            return;
        }

        // Clear input and hide error
        chatInput.value = "";
        updateCharCount();
        autoResizeTextarea();
        updateSendButton();
        hideError();

        // Add user message to chat
        appendMessage("user", userMessage);

        // Show typing indicator
        showTypingIndicator();

        // Disable form during request
        setFormDisabled(true);

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response
            appendMessage("bot", data.reply);

        } catch (error) {
            console.error("Error sending message:", error);
            hideTypingIndicator();
            
            let errorMsg = "Sorry, I'm having trouble responding right now. Please try again.";
            
            if (error.message.includes("Failed to fetch")) {
                errorMsg = "Connection error. Please check your internet connection and try again.";
            } else if (error.message.includes("HTTP 500")) {
                errorMsg = "Server error. Please try again in a moment.";
            } else if (error.message.includes("HTTP 400")) {
                errorMsg = "Invalid message format. Please try rephrasing your message.";
            }
            
            showError(errorMsg);
        } finally {
            // Re-enable form
            setFormDisabled(false);
            chatInput.focus();
        }
    }

    function appendMessage(sender, message) {
        const messageGroup = document.createElement("div");
        messageGroup.className = "message-group";

        const messageDiv = document.createElement("div");
        messageDiv.className = sender === "user" ? "user-message" : "bot-message";

        const messageContent = document.createElement("div");
        messageContent.className = "message-content";
        messageContent.textContent = message;

        const messageTime = document.createElement("div");
        messageTime.className = "message-time";
        messageTime.textContent = getCurrentTime();

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        messageGroup.appendChild(messageDiv);

        chatLog.appendChild(messageGroup);
        scrollToBottom();
    }

    function showTypingIndicator() {
        typingIndicator.style.display = "flex";
        scrollToBottom();
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = "none";
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = "block";
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            hideError();
        }, 5000);
    }

    function hideError() {
        errorMessage.style.display = "none";
    }

    function setFormDisabled(disabled) {
        chatInput.disabled = disabled;
        sendButton.disabled = disabled;
        
        if (disabled) {
            sendButton.style.opacity = "0.6";
            chatInput.style.opacity = "0.7";
        } else {
            updateSendButton();
            chatInput.style.opacity = "1";
        }
    }

    function scrollToBottom() {
        setTimeout(() => {
            chatLog.scrollTop = chatLog.scrollHeight;
        }, 100);
    }

    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });
    }

    // Handle page visibility change to refocus input
    document.addEventListener("visibilitychange", function() {
        if (!document.hidden) {
            setTimeout(() => {
                chatInput.focus();
            }, 100);
        }
    });

    // Handle window resize
    window.addEventListener("resize", function() {
        scrollToBottom();
    });

    // Prevent form submission on page reload
    window.addEventListener("beforeunload", function() {
        if (chatInput.value.trim()) {
            return "You have an unsent message. Are you sure you want to leave?";
        }
    });
});
