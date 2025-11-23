// Use relative URL since frontend is served from the same origin
const API_BASE_URL = '';
let currentChatId = null;
let chatHistory = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    const newChatBtn = document.getElementById('newChatBtn');

    sendBtn.addEventListener('click', sendMessage);
    newChatBtn.addEventListener('click', startNewChat);

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// Start a new chat
function startNewChat() {
    currentChatId = null;
    clearChatMessages();
    document.getElementById('messageInput').focus();
    updateActiveChatInHistory();
}

// Send message
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';

    // Show thinking indicator
    showThinkingIndicator();

    // Disable input
    setInputEnabled(false);

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_message: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Hide thinking indicator
        hideThinkingIndicator();

        // Add assistant response
        addMessage('assistant', data.response);

        // Save to chat history
        saveToChatHistory(message, data.response, data.message_history);

    } catch (error) {
        hideThinkingIndicator();
        addMessage('assistant', `Error: ${error.message}. Please try again.`);
        console.error('Error:', error);
    } finally {
        setInputEnabled(true);
        messageInput.focus();
    }
}

// Add message to chat
function addMessage(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Remove welcome message if it exists
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format message content (handle markdown-like formatting)
    contentDiv.innerHTML = formatMessage(content);

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message content
function formatMessage(content) {
    // Escape HTML first
    let formatted = escapeHtml(content);
    
    // Convert line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Convert code blocks (```code```)
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Convert inline code (`code`)
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert bold (**text**)
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert italic (*text*)
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Convert lists (- item)
    formatted = formatted.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    return formatted;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show thinking indicator
function showThinkingIndicator() {
    document.getElementById('thinkingIndicator').style.display = 'block';
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide thinking indicator
function hideThinkingIndicator() {
    document.getElementById('thinkingIndicator').style.display = 'none';
}

// Set input enabled/disabled
function setInputEnabled(enabled) {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    
    messageInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
}

// Clear chat messages
function clearChatMessages() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h3>Welcome! 👋</h3>
            <p>Start a conversation by typing a message below.</p>
        </div>
    `;
}

// Save to chat history
function saveToChatHistory(userMessage, assistantMessage, messageHistory) {
    if (!currentChatId) {
        currentChatId = Date.now().toString();
    }

    const chat = chatHistory.find(c => c.id === currentChatId);
    
    if (chat) {
        chat.messages.push({
            role: 'user',
            content: userMessage,
            timestamp: new Date().toISOString()
        });
        chat.messages.push({
            role: 'assistant',
            content: assistantMessage,
            timestamp: new Date().toISOString(),
            messageHistory: messageHistory
        });
        chat.lastMessage = assistantMessage.substring(0, 50);
        chat.updatedAt = new Date().toISOString();
    } else {
        chatHistory.unshift({
            id: currentChatId,
            title: userMessage.substring(0, 50),
            lastMessage: assistantMessage.substring(0, 50),
            messages: [
                {
                    role: 'user',
                    content: userMessage,
                    timestamp: new Date().toISOString()
                },
                {
                    role: 'assistant',
                    content: assistantMessage,
                    timestamp: new Date().toISOString(),
                    messageHistory: messageHistory
                }
            ],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        });
    }

    saveChatHistoryToStorage();
    renderChatHistory();
    updateActiveChatInHistory();
}

// Load chat history from localStorage
function loadChatHistory() {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        chatHistory = JSON.parse(saved);
        renderChatHistory();
    }
}

// Save chat history to localStorage
function saveChatHistoryToStorage() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

// Render chat history sidebar
function renderChatHistory() {
    const historyList = document.getElementById('chatHistory');
    
    if (chatHistory.length === 0) {
        historyList.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">No chat history yet</div>';
        return;
    }

    historyList.innerHTML = chatHistory.map(chat => {
        const date = new Date(chat.updatedAt);
        const timeStr = date.toLocaleString();
        
        return `
            <div class="chat-history-item" data-chat-id="${chat.id}">
                <div class="chat-history-item-title">${escapeHtml(chat.title)}</div>
                <div class="chat-history-item-time">${timeStr}</div>
            </div>
        `;
    }).join('');

    // Add click listeners
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.addEventListener('click', () => {
            const chatId = item.dataset.chatId;
            loadChat(chatId);
        });
    });
}

// Load a specific chat
function loadChat(chatId) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;

    currentChatId = chatId;
    clearChatMessages();

    // Load all messages
    chat.messages.forEach(msg => {
        addMessage(msg.role, msg.content);
    });

    updateActiveChatInHistory();
}

// Update active chat in history
function updateActiveChatInHistory() {
    document.querySelectorAll('.chat-history-item').forEach(item => {
        if (item.dataset.chatId === currentChatId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

