// Use relative URL since frontend is served from the same origin
// Empty string means use the same origin (no need for full URL)
const API_BASE_URL = '';

// Store the current active chat session ID (null means new chat)
let currentChatId = null;

// Array to store all chat conversations in memory
let chatHistory = [];

// Initialize the application when the DOM is fully loaded
// This ensures all HTML elements exist before we try to access them
document.addEventListener('DOMContentLoaded', () => {
    // Load previously saved chat history from browser's localStorage
    LoadChatHistoryFromAPI();
    // Set up all event listeners for buttons and input fields
    setupEventListeners();
});

// Setup event listeners for user interactions
function setupEventListeners() {
    // Get references to DOM elements by their IDs
    const sendBtn = document.getElementById('sendBtn');        // Send button element
    const messageInput = document.getElementById('messageInput'); // Text input field element
    const newChatBtn = document.getElementById('newChatBtn');     // New chat button element

    // Add click event listener to send button - calls sendMessage when clicked
    sendBtn.addEventListener('click', sendMessage);
    // Add click event listener to new chat button - calls startNewChat when clicked
    newChatBtn.addEventListener('click', startNewChat);

    // Add keyboard event listener to message input field
    messageInput.addEventListener('keydown', (e) => {
        // Check if Enter key was pressed (but not Shift+Enter, which allows new line)
        if (e.key === 'Enter' && !e.shiftKey) {
            // Prevent default behavior (form submission or new line)
            e.preventDefault();
            // Send the message when Enter is pressed
            sendMessage();
        }
    });
}

// Start a new chat conversation
function startNewChat() {
    // Reset current chat ID to null (indicates a new chat session)
    currentChatId = null;
    // Clear all messages from the chat display area
    clearChatMessages();
    // Focus the cursor on the message input field for immediate typing
    document.getElementById('messageInput').focus();
    // Update the visual indicator showing which chat is active in the sidebar
    updateActiveChatInHistory();
}

// Send a message to the AI assistant
async function sendMessage() {
    // Get reference to the message input field
    const messageInput = document.getElementById('messageInput');
    // Get the message text and remove leading/trailing whitespace
    const message = messageInput.value.trim();

    // If message is empty, do nothing (prevent sending empty messages)
    if (!message) return;

    // Add the user's message to the chat display immediately
    addMessage('user', message);
    // Clear the input field after sending
    messageInput.value = '';

    // Show a "thinking" indicator to let user know the AI is processing
    showThinkingIndicator();

    // Disable input field and send button to prevent multiple submissions
    setInputEnabled(false);

    try {
        const requestBody = {
            user_message: message
        };
        if (currentChatId) {
            requestBody.chat_id = currentChatId;
        }
        // Send POST request to the /chat API endpoint
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',  // HTTP method for sending data
            headers: {
                'Content-Type': 'application/json',  // Tell server we're sending JSON
            },
            // Convert JavaScript object to JSON string for the request body
            body: JSON.stringify(requestBody)
        });

        // Check if the HTTP response indicates an error (status code >= 400)
        if (!response.ok) {
            
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Parse the JSON response from the server into a JavaScript object
        const data = await response.json();
        
        // Hide the "thinking" indicator since we got a response
        hideThinkingIndicator();

        // update current chat id if it is returned from the server
        if (data.chat_id) {
            currentChatId = data.chat_id
        }

        // Add the assistant's response to the chat display
        addMessage('assistant', data.response);

        await LoadChatHistoryFromAPI();

        updateActiveChatInHistory();


    } catch (error) {
        // If an error occurred, hide the thinking indicator
        hideThinkingIndicator();
        // Display an error message to the user
        addMessage('assistant', `Error: ${error.message}. Please try again.`);
        // Log the error to browser console for debugging
        console.error('Error:', error);
    } finally {
        // Re-enable input field and send button (runs whether success or error)
        setInputEnabled(true);
        // Return focus to the input field for the next message
        messageInput.focus();
    }
}

// Add a message to the chat display area
function addMessage(role, content) {
    // Get reference to the container that holds all chat messages
    const chatMessages = document.getElementById('chatMessages');
    
    // Remove welcome message if it exists (first message removes the welcome screen)
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        // Remove the welcome message element from the DOM
        welcomeMsg.remove();
    }

    // Create a new div element to hold this message
    const messageDiv = document.createElement('div');
    // Add CSS classes: 'message' for base styling, and 'user' or 'assistant' for role-specific styling
    messageDiv.className = `message ${role}`;

    // Create a div to hold the actual message content
    const contentDiv = document.createElement('div');
    // Add CSS class for message content styling
    contentDiv.className = 'message-content';
    
    // Format the message content (convert markdown to HTML, escape HTML, etc.)
    contentDiv.innerHTML = formatMessage(content);

    // Add the content div to the message div
    messageDiv.appendChild(contentDiv);
    // Add the complete message div to the chat messages container
    chatMessages.appendChild(messageDiv);

    // Automatically scroll to the bottom to show the latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message content: convert markdown-style formatting to HTML
function formatMessage(content) {
    // First escape any HTML characters to prevent XSS attacks (convert < to &lt;, etc.)
    let formatted = escapeHtml(content);
    
    // Convert newline characters (\n) to HTML line breaks (<br>)
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Convert code blocks: ```code``` becomes <pre><code>code</pre></code>
    // [\s\S]*? matches any characters (including newlines) non-greedily
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Convert inline code: `code` becomes <code>code</code>
    // [^`]+ matches one or more characters that are not backticks
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert bold text: **text** becomes <strong>text</strong>
    // .+? matches one or more characters non-greedily
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert italic text: *text* becomes <em>text</em>
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Convert list items: - item or • item becomes <li>item</li>
    // ^ means start of line, $ means end of line, gm flags: global and multiline
    formatted = formatted.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
    // Wrap consecutive list items in <ul> tags
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Return the fully formatted HTML string
    return formatted;
}

// Escape HTML special characters to prevent XSS (Cross-Site Scripting) attacks
function escapeHtml(text) {
    // Create a temporary div element (not added to page)
    const div = document.createElement('div');
    // Set the text content (browser automatically escapes HTML)
    div.textContent = text;
    // Get the innerHTML which now has escaped characters (&lt; instead of <, etc.)
    return div.innerHTML;
}

// Show the "thinking" indicator while waiting for AI response
function showThinkingIndicator() {
    // Make the thinking indicator visible by changing display style
    document.getElementById('thinkingIndicator').style.display = 'block';
    // Get reference to chat messages container
    const chatMessages = document.getElementById('chatMessages');
    // Scroll to bottom to show the thinking indicator
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide the "thinking" indicator when response is received
function hideThinkingIndicator() {
    // Hide the thinking indicator by changing display style to none
    document.getElementById('thinkingIndicator').style.display = 'none';
}

// Enable or disable the input field and send button
function setInputEnabled(enabled) {
    // Get references to input field and send button
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    
    // Set disabled property: if enabled is true, disabled is false (and vice versa)
    messageInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
}

// Clear all messages from the chat display and show welcome message
function clearChatMessages() {
    // Get reference to chat messages container
    const chatMessages = document.getElementById('chatMessages');
    // Replace all content with welcome message HTML
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h3>Welcome! 👋</h3>
            <p>Start a conversation by typing a message below.</p>
        </div>
    `;
}


// Load chat history from browser's localStorage (persistent storage)
function loadChatHistory() {
    // Get saved chat history from localStorage (returns null if nothing saved)
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        // Parse the JSON string back into a JavaScript array
        chatHistory = JSON.parse(saved);
        // Render the chat history in the sidebar
        renderChatHistory();
    }
}

// Render the chat history list in the sidebar
function renderChatHistory() {
    // Get reference to the history list container element
    const historyList = document.getElementById('chatHistory');
    
    // If no chat history exists, show a placeholder message
    if (chatHistory.length === 0) {
        // Set innerHTML to show "No chat history yet" message
        historyList.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">No chat history yet</div>';
        // Exit function early
        return;
    }

    // Generate HTML for each chat in history using map function
    historyList.innerHTML = chatHistory.map(chat => {
        // Convert ISO timestamp to readable date/time string
        const date = new Date(chat.updatedAt);
        const timeStr = date.toLocaleString();
        
        // Return HTML string for this chat item
        return `
            <div class="chat-history-item" data-chat-id="${chat.id}">
                <div class="chat-history-item-title">${escapeHtml(chat.title)}</div>
                <div class="chat-history-item-time">${timeStr}</div>
            </div>
        `;
    }).join('');  // Join all HTML strings into one string (removes commas)

    // Add click event listeners to each chat history item
    document.querySelectorAll('.chat-history-item').forEach(item => {
        // When a chat item is clicked, load that chat
        item.addEventListener('click', () => {
            // Get the chat ID from the data attribute
            const chatId = item.dataset.chatId;
            // Load and display that chat
            loadChat(chatId);
        });
    });
}

// Load and display a specific chat conversation
async function loadChat(chatId) {
    try {
        // Set this chat as the current active chat
        currentChatId = chatId;
        
        // Clear the current chat display
        clearChatMessages();
        
        // Show loading indicator
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">Loading messages...</div>';
        
        // Fetch messages from API endpoint (GET /api/messages/{chat_id})
        const response = await fetch(`${API_BASE_URL}/messages/${chatId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const messages = data.messages || [];
        
        // Clear loading message
        chatMessages.innerHTML = '';
        
        // If no messages found, show welcome message
        if (messages.length === 0) {
            clearChatMessages();
            return;
        }
        
        // Loop through all messages and display them
        messages.forEach(msg => {
            // Add each message to the display (role: 'user' or 'assistant', content: message text)
            addMessage(msg.role, msg.content);
        });

        // Update the visual indicator showing which chat is active
        updateActiveChatInHistory();
        
    } catch (error) {
        console.error('Error loading chat:', error);
        // Show error message
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #f00;">
                Error loading chat: ${error.message}
            </div>
        `;
    }
}

// Update the visual highlight of the active chat in the history sidebar
function updateActiveChatInHistory() {
    // Loop through all chat history items in the sidebar
    document.querySelectorAll('.chat-history-item').forEach(item => {
        // Check if this item's chat ID matches the current active chat ID
        if (item.dataset.chatId === currentChatId) {
            // Add 'active' CSS class to highlight this chat
            item.classList.add('active');
        } else {
            // Remove 'active' CSS class from other chats
            item.classList.remove('active');
        }
    });
}

async function LoadChatHistoryFromAPI() {
    try {
        const response = await fetch(`${API_BASE_URL}/all_chats`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const chats = data.chats || [];
        chatHistory = chats.map(chat => ({
            id: chat.chat_id,
            title: chat.title,
            updatedAt: chat.created_at || new Date().toISOString()
        }));
        renderChatHistory();
    } catch (error) {
        console.error('Error loading chat history:', error);
        const historylist = document.getElementById('chatHistory');
        historylist.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">Error loading chat history</div>';
    }
}
