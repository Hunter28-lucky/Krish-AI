// ===================================
// Configuration
// ===================================
const API_URL = '/api/chat';  // Will be handled by Vercel serverless function

// ===================================
// State Management
// ===================================
let messages = [];
let isLoading = false;
let chatHistories = JSON.parse(localStorage.getItem('chatHistories') || '[]');
let currentChatId = null;

// ===================================
// Theme Management
// ===================================
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update icon
    const themeIcon = document.querySelector('.theme-icon');
    themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
}

// Load saved theme
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    const themeIcon = document.querySelector('.theme-icon');
    themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
}

// ===================================
// Sidebar Toggle (Mobile)
// ===================================
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// ===================================
// Chat Functions
// ===================================
function clearChat() {
    // Save current chat if it has messages
    if (messages.length > 0) {
        saveCurrentChat();
    }
    
    messages = [];
    currentChatId = Date.now().toString();
    document.getElementById('messages').innerHTML = '';
    document.getElementById('welcomeMessage').style.display = 'block';
    document.getElementById('inputActions').style.display = 'none';
    
    // Close sidebar on mobile
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.remove('open');
}

function saveCurrentChat() {
    if (messages.length === 0) return;
    
    const firstMessage = messages[0].content.substring(0, 30) + '...';
    const chat = {
        id: currentChatId || Date.now().toString(),
        title: firstMessage,
        messages: messages,
        timestamp: Date.now()
    };
    
    // Remove existing chat with same ID
    chatHistories = chatHistories.filter(c => c.id !== chat.id);
    
    // Add to beginning
    chatHistories.unshift(chat);
    
    // Keep only last 20 chats
    chatHistories = chatHistories.slice(0, 20);
    
    localStorage.setItem('chatHistories', JSON.stringify(chatHistories));
    renderChatHistory();
}

function loadChat(chatId) {
    const chat = chatHistories.find(c => c.id === chatId);
    if (!chat) return;
    
    // Save current chat first
    if (messages.length > 0 && currentChatId !== chatId) {
        saveCurrentChat();
    }
    
    currentChatId = chat.id;
    messages = chat.messages;
    
    // Render messages
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    document.getElementById('welcomeMessage').style.display = 'none';
    
    messages.forEach(msg => {
        addMessageToUI(msg.role, msg.content);
    });
    
    document.getElementById('inputActions').style.display = 'flex';
    
    // Close sidebar on mobile
    document.querySelector('.sidebar').classList.remove('open');
}

function renderChatHistory() {
    const container = document.getElementById('chatHistory');
    
    if (chatHistories.length === 0) {
        container.innerHTML = '<p class="no-history">No chat history yet</p>';
        return;
    }
    
    container.innerHTML = chatHistories.map(chat => `
        <div class="chat-history-item" onclick="loadChat('${chat.id}')">
            <span class="history-icon">💬</span>
            <span class="history-text">${escapeHtml(chat.title)}</span>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function regenerateResponse() {
    if (messages.length < 2) return;
    
    // Remove last assistant message
    messages.pop();
    
    // Get the last user message
    const lastUserMessage = messages[messages.length - 1].content;
    
    // Remove last user message
    messages.pop();
    
    // Remove last two messages from UI
    const messagesContainer = document.getElementById('messages');
    const messageElements = messagesContainer.querySelectorAll('.message');
    if (messageElements.length >= 2) {
        messageElements[messageElements.length - 1].remove();
        messageElements[messageElements.length - 2].remove();
    }
    
    // Re-send the message
    document.getElementById('userInput').value = lastUserMessage;
    sendMessage();
}

function copyLastResponse() {
    const lastAssistantMessage = messages.filter(m => m.role === 'assistant').pop();
    if (lastAssistantMessage) {
        navigator.clipboard.writeText(lastAssistantMessage.content).then(() => {
            showToast('Copied to clipboard!');
        });
    }
}

function copyMessage(button, content) {
    navigator.clipboard.writeText(content).then(() => {
        button.classList.add('copied');
        button.innerHTML = '✓';
        setTimeout(() => {
            button.classList.remove('copied');
            button.innerHTML = '📋';
        }, 2000);
    });
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--text-primary);
        color: var(--bg-primary);
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 1000;
        animation: fadeIn 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}

function usePrompt(prompt) {
    document.getElementById('userInput').value = prompt;
    document.getElementById('welcomeMessage').style.display = 'none';
    sendMessage();
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

function setLoading(loading, text = 'Thinking...') {
    isLoading = loading;
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const sendBtn = document.getElementById('sendBtn');
    
    if (loading) {
        overlay.classList.add('active');
        loadingText.textContent = text;
        sendBtn.disabled = true;
    } else {
        overlay.classList.remove('active');
        sendBtn.disabled = false;
    }
}

function formatMessage(text) {
    // Clean and convert markdown to HTML - natural chat style
    let formatted = text;
    
    // Step 1: Clean up raw HTML tags that shouldn't be there
    formatted = formatted.replace(/<br\s*\/?>/gi, '\n');
    formatted = formatted.replace(/<\/?p>/gi, '\n');
    formatted = formatted.replace(/<\/?div>/gi, '\n');
    formatted = formatted.replace(/<\/?span>/gi, '');
    
    // Step 2: Remove markdown tables and convert to simple text
    formatted = formatted.replace(/\|[^\n]+\|/g, (match) => {
        // Convert table row to simple comma-separated text
        return match.replace(/\|/g, ' ').replace(/[-:]+/g, '').trim();
    });
    formatted = formatted.replace(/^[\s]*[-:]+[\s]*$/gm, ''); // Remove table separators
    
    // Step 3: Escape HTML for safety
    formatted = formatted.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Step 4: Process code blocks FIRST (preserve them)
    const codeBlocks = [];
    formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        const placeholder = `__CODEBLOCK_${codeBlocks.length}__`;
        codeBlocks.push(`<div class="code-block"><div class="code-header"><span class="code-lang">${lang || 'code'}</span><button class="copy-code-btn" onclick="copyCode(this)">📋 Copy</button></div><pre><code>${code.trim()}</code></pre></div>`);
        return placeholder;
    });
    
    // Step 5: Inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Step 6: Bold and italic
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Step 7: Links
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Step 8: Headers (smaller, less intrusive)
    formatted = formatted.replace(/^#{1,4}\s+(.*?)$/gm, '<strong>$1</strong>');
    
    // Step 9: Simple bullet points
    formatted = formatted.replace(/^[\-\*]\s+(.*?)$/gm, '• $1');
    
    // Step 10: Numbered lists - keep simple
    formatted = formatted.replace(/^(\d+)\.\s+(.*?)$/gm, '$1. $2');
    
    // Step 11: Blockquotes
    formatted = formatted.replace(/^&gt;\s*(.*?)$/gm, '<blockquote>$1</blockquote>');
    
    // Step 12: Convert paragraphs naturally
    // Split by double newlines for paragraphs
    const paragraphs = formatted.split(/\n\n+/);
    formatted = paragraphs.map(p => {
        p = p.trim();
        if (!p) return '';
        // Check for code block placeholders
        if (p.includes('__CODEBLOCK_')) return p;
        // Check if it's already a block element
        if (p.startsWith('<blockquote') || p.startsWith('<div')) return p;
        // Convert single newlines within paragraph to <br>
        p = p.replace(/\n/g, '<br>');
        return `<p>${p}</p>`;
    }).filter(p => p).join('');
    
    // Step 13: Restore code blocks
    codeBlocks.forEach((block, i) => {
        formatted = formatted.replace(`__CODEBLOCK_${i}__`, block);
    });
    
    // Step 14: Clean up
    formatted = formatted.replace(/<p><\/p>/g, '');
    formatted = formatted.replace(/<br><br>/g, '</p><p>');
    formatted = formatted.replace(/(<br>\s*)+$/g, '');
    
    return formatted;
}

function copyCode(button) {
    const codeBlock = button.closest('.code-block').querySelector('code');
    navigator.clipboard.writeText(codeBlock.textContent).then(() => {
        button.innerHTML = '✓ Copied';
        setTimeout(() => {
            button.innerHTML = '📋 Copy';
        }, 2000);
    });
}

function addMessage(role, content, searchInfo = null) {
    addMessageToUI(role, content, searchInfo);
    
    // Show input actions after first exchange
    if (messages.length >= 2) {
        document.getElementById('inputActions').style.display = 'flex';
    }
    
    // Auto-save chat
    saveCurrentChat();
}

function addMessageToUI(role, content, searchInfo = null) {
    const messagesContainer = document.getElementById('messages');
    const welcomeMessage = document.getElementById('welcomeMessage');
    
    // Hide welcome message
    welcomeMessage.style.display = 'none';
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const avatar = role === 'user' ? '👤' : '✨';
    const senderName = role === 'user' ? 'You' : 'Krish AI';
    
    let searchStatusHTML = '';
    if (searchInfo && searchInfo.searches && searchInfo.searches.length > 0) {
        searchStatusHTML = `
            <div class="search-status">
                <div class="search-status-header">
                    <span>🔍</span>
                    <span>Searched the web</span>
                </div>
                ${searchInfo.searches.map(s => `
                    <div class="search-item">
                        <span class="search-item-icon">✓</span>
                        <span>${s.query}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Message actions (copy button)
    const actionsHTML = role === 'assistant' ? `
        <div class="message-actions">
            <button class="msg-action-btn" onclick="copyMessage(this, \`${content.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)" title="Copy">📋</button>
        </div>
    ` : '';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${senderName}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-bubble">
                ${formatMessage(content)}
            </div>
            ${searchStatusHTML}
            ${actionsHTML}
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addTypingIndicator() {
    const messagesContainer = document.getElementById('messages');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typingIndicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">✨</div>
        <div class="message-content">
            <div class="message-bubble">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const userMessage = input.value.trim();
    
    if (!userMessage || isLoading) return;
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Add user message to UI
    addMessage('user', userMessage);
    
    // Add to messages array
    messages.push({ role: 'user', content: userMessage });
    
    // Show loading
    setLoading(true, '🧠 Analyzing your question...');
    addTypingIndicator();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messages,
                userMessage: userMessage
            })
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add assistant message to UI
        addMessage('assistant', data.content, data.searchInfo);
        
        // Add to messages array
        messages.push({ role: 'assistant', content: data.content });
        
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
        setLoading(false);
    }
}

// ===================================
// Initialize
// ===================================
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    renderChatHistory();
    currentChatId = Date.now().toString();
    
    // Focus input
    document.getElementById('userInput').focus();
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        const sidebar = document.querySelector('.sidebar');
        const menuToggle = document.querySelector('.menu-toggle');
        
        if (sidebar.classList.contains('open') && 
            !sidebar.contains(e.target) && 
            !menuToggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
});
