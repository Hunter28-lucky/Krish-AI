// ============================================
// Configuration
// ============================================
const API_URL = '/api/chat';

// ============================================
// State
// ============================================
let messages = [];
let isLoading = false;
let chatHistories = JSON.parse(localStorage.getItem('chatHistories') || '[]');
let currentChatId = null;

// ============================================
// Theme
// ============================================
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.body.setAttribute('data-theme', savedTheme);
}

// ============================================
// Sidebar
// ============================================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const isOpen = sidebar.classList.contains('open');
    
    if (isOpen) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    } else {
        sidebar.classList.add('open');
        overlay.classList.add('active');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
}

// ============================================
// Chat Management
// ============================================
function clearChat() {
    if (messages.length > 0) {
        saveCurrentChat();
    }
    
    messages = [];
    currentChatId = Date.now().toString();
    document.getElementById('messages').innerHTML = '';
    document.getElementById('welcome').style.display = 'flex';
    closeSidebar();
}

function saveCurrentChat() {
    if (messages.length === 0) return;
    
    const firstUserMsg = messages.find(m => m.role === 'user');
    const title = firstUserMsg 
        ? firstUserMsg.content.substring(0, 40) + (firstUserMsg.content.length > 40 ? '...' : '')
        : 'New chat';
    
    const chat = {
        id: currentChatId || Date.now().toString(),
        title: title,
        messages: messages,
        timestamp: Date.now()
    };
    
    chatHistories = chatHistories.filter(c => c.id !== chat.id);
    chatHistories.unshift(chat);
    chatHistories = chatHistories.slice(0, 20);
    
    localStorage.setItem('chatHistories', JSON.stringify(chatHistories));
    renderChatHistory();
}

function loadChat(chatId) {
    const chat = chatHistories.find(c => c.id === chatId);
    if (!chat) return;
    
    if (messages.length > 0 && currentChatId !== chatId) {
        saveCurrentChat();
    }
    
    currentChatId = chat.id;
    messages = [...chat.messages];
    
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    document.getElementById('welcome').style.display = 'none';
    
    messages.forEach(msg => {
        appendMessage(msg.role, msg.content);
    });
    
    closeSidebar();
}

function renderChatHistory() {
    const container = document.getElementById('chatHistory');
    
    if (chatHistories.length === 0) {
        container.innerHTML = '<p class="empty-state">No previous chats</p>';
        return;
    }
    
    container.innerHTML = chatHistories.map(chat => `
        <div class="history-item ${chat.id === currentChatId ? 'active' : ''}" onclick="loadChat('${chat.id}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>${escapeHtml(chat.title)}</span>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Message Formatting
// ============================================
function formatMessage(text) {
    let formatted = text;
    
    // Clean HTML tags
    formatted = formatted.replace(/<br\s*\/?>/gi, '\n');
    formatted = formatted.replace(/<\/?p>/gi, '\n');
    formatted = formatted.replace(/<\/?div>/gi, '\n');
    formatted = formatted.replace(/<\/?span>/gi, '');
    
    // Remove markdown tables
    formatted = formatted.replace(/\|[^\n]+\|/g, match => {
        return match.replace(/\|/g, ' ').replace(/[-:]+/g, '').trim();
    });
    formatted = formatted.replace(/^[\s]*[-:]+[\s]*$/gm, '');
    
    // Escape HTML
    formatted = formatted.replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Code blocks
    const codeBlocks = [];
    formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        const placeholder = `__CODE_${codeBlocks.length}__`;
        codeBlocks.push(`
            <div class="code-block">
                <div class="code-header">
                    <span class="code-lang">${lang || 'code'}</span>
                    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                </div>
                <pre><code>${code.trim()}</code></pre>
            </div>
        `);
        return placeholder;
    });
    
    // Inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold and italic
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Links
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Headers -> bold
    formatted = formatted.replace(/^#{1,4}\s+(.*?)$/gm, '<strong>$1</strong>');
    
    // Lists
    formatted = formatted.replace(/^[\-\*]\s+(.*?)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/^(\d+)\.\s+(.*?)$/gm, '<li>$2</li>');
    
    // Blockquotes
    formatted = formatted.replace(/^&gt;\s*(.*?)$/gm, '<blockquote>$1</blockquote>');
    
    // Paragraphs
    const paragraphs = formatted.split(/\n\n+/);
    formatted = paragraphs.map(p => {
        p = p.trim();
        if (!p) return '';
        if (p.includes('__CODE_')) return p;
        if (p.startsWith('<blockquote') || p.startsWith('<li>')) return p;
        p = p.replace(/\n/g, '<br>');
        return `<p>${p}</p>`;
    }).filter(Boolean).join('');
    
    // Wrap consecutive <li> in <ul>
    formatted = formatted.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
    
    // Restore code blocks
    codeBlocks.forEach((block, i) => {
        formatted = formatted.replace(`__CODE_${i}__`, block);
    });
    
    // Cleanup
    formatted = formatted.replace(/<p><\/p>/g, '');
    
    return formatted;
}

function copyCode(button) {
    const code = button.closest('.code-block').querySelector('code');
    navigator.clipboard.writeText(code.textContent).then(() => {
        button.textContent = 'Copied!';
        setTimeout(() => button.textContent = 'Copy', 2000);
    });
}

function copyMessage(content, button) {
    navigator.clipboard.writeText(content).then(() => {
        button.classList.add('copied');
        button.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 6L9 17l-5-5"/>
            </svg>
        `;
        setTimeout(() => {
            button.classList.remove('copied');
            button.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
            `;
        }, 2000);
    });
}

// ============================================
// Message Display
// ============================================
function appendMessage(role, content) {
    const container = document.getElementById('messages');
    const welcome = document.getElementById('welcome');
    welcome.style.display = 'none';
    
    const div = document.createElement('div');
    div.className = `message ${role}`;
    
    const avatar = role === 'user' ? 'You' : 'K';
    const sender = role === 'user' ? 'You' : 'Krish AI';
    
    const escapedContent = content.replace(/`/g, '\\`').replace(/\$/g, '\\$');
    
    div.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-body">
            <div class="message-sender">${sender}</div>
            <div class="message-content">${formatMessage(content)}</div>
            ${role === 'assistant' ? `
                <div class="message-actions">
                    <button class="action-btn" onclick="copyMessage(\`${escapedContent}\`, this)" title="Copy">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                        </svg>
                    </button>
                </div>
            ` : ''}
        </div>
    `;
    
    container.appendChild(div);
    scrollToBottom();
}

function addTypingIndicator() {
    const container = document.getElementById('messages');
    
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'typingIndicator';
    
    div.innerHTML = `
        <div class="message-avatar">K</div>
        <div class="message-body">
            <div class="message-sender">Krish AI</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(div);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

function scrollToBottom() {
    const chat = document.getElementById('chat');
    chat.scrollTop = chat.scrollHeight;
}

// ============================================
// Input Handling
// ============================================
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

function usePrompt(prompt) {
    document.getElementById('userInput').value = prompt;
    document.getElementById('welcome').style.display = 'none';
    sendMessage();
}

function setLoading(loading) {
    isLoading = loading;
    const btn = document.getElementById('sendBtn');
    btn.disabled = loading;
}

// ============================================
// Send Message
// ============================================
async function sendMessage() {
    const input = document.getElementById('userInput');
    const userMessage = input.value.trim();
    
    if (!userMessage || isLoading) return;
    
    input.value = '';
    input.style.height = 'auto';
    
    // Add user message
    appendMessage('user', userMessage);
    messages.push({ role: 'user', content: userMessage });
    
    setLoading(true);
    addTypingIndicator();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: messages,
                userMessage: userMessage
            })
        });
        
        if (!response.ok) throw new Error('Request failed');
        
        const data = await response.json();
        
        removeTypingIndicator();
        appendMessage('assistant', data.content);
        messages.push({ role: 'assistant', content: data.content });
        
        saveCurrentChat();
        
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        appendMessage('assistant', 'Something went wrong. Please try again.');
    } finally {
        setLoading(false);
    }
}

// ============================================
// Initialize
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    renderChatHistory();
    currentChatId = Date.now().toString();
    document.getElementById('userInput').focus();
});
