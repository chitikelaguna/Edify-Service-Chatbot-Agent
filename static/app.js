// Configuration
const API_BASE_URL = window.location.origin; // Use same origin as frontend
let currentSessionId = null;

// DOM Elements
const chatSection = document.getElementById('chatSection');
const chatForm = document.getElementById('chatForm');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const sessionIdDisplay = document.getElementById('sessionIdDisplay');

// Initialize - Auto-start session
document.addEventListener('DOMContentLoaded', async () => {
    // Check if session exists in localStorage
    const savedSession = localStorage.getItem('chatSession');
    
    if (savedSession) {
        currentSessionId = savedSession;
        showChatSection();
    } else {
        // Try to auto-create a new session, but don't block if it fails
        await startSession();
        // Show chat section even if session creation failed
        // User can still send messages - backend will handle session creation
        if (!currentSessionId) {
            showChatSection();
        }
    }
});

// Auto-start session function
async function startSession() {
    try {
        const response = await fetch(`${API_BASE_URL}/session/start-anonymous`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Failed to start session' }));
            throw new Error(errorData.detail || 'Failed to start session');
        }
        
        const data = await response.json();
        currentSessionId = data.session_id;
        
        // Save to localStorage
        localStorage.setItem('chatSession', currentSessionId);
        
        showChatSection();
        return true;
        
    } catch (error) {
        console.error('Error starting session:', error);
        // Don't show error message immediately - let user try to send a message
        // The backend will create a session automatically when needed
        return false;
    }
}

// Chat Form Handler
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    
    // Disable input while processing
    messageInput.disabled = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="loading"></span>';
    
    try {
        // Ensure we have a session - create one if needed
        if (!currentSessionId) {
            try {
                await startSession();
            } catch (sessionError) {
                console.error('Session creation failed, will use temporary session ID:', sessionError);
                // Generate a temporary session ID if creation fails
                currentSessionId = 'temp-' + Date.now();
            }
        }
        
        const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId || 'temp-' + Date.now()
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP ${response.status}: Failed to get response`);
        }
        
        const data = await response.json();
        
        // Update session ID if backend created a new one
        if (data.session_id && data.session_id !== currentSessionId) {
            currentSessionId = data.session_id;
            localStorage.setItem('chatSession', currentSessionId);
            sessionIdDisplay.textContent = `Session: ${currentSessionId.substring(0, 8)}...`;
        }
        
        addMessage('assistant', data.response);
        
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('assistant', `Error: ${error.message || 'Failed to send message. Please try again.'}`);
    } finally {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span>Send</span>';
        messageInput.focus();
    }
});

// Helper Functions
function showChatSection() {
    if (currentSessionId) {
        sessionIdDisplay.textContent = `Session: ${currentSessionId.substring(0, 8)}...`;
    }
    messageInput.focus();
    // Add welcome guide message (frontend-only, no backend call)
    if (chatMessages.children.length === 0) {
        showWelcomeGuide();
    }
}

function showWelcomeGuide() {
    const guideContent = `
<h3>Welcome to Edify Admin AI Assistant</h3>
<p>This chatbot helps Edify admins get quick answers from verified Edify data.</p>
<strong>You can ask questions related to:</strong>
<div class="category-grid">
    <div class="category-item">
        <span class="icon">CRM</span>
        <span>CRM data (leads, counts, statuses)</span>
    </div>
    <div class="category-item">
        <span class="icon">LMS</span>
        <span>LMS data (batches, courses, enrollments)</span>
    </div>
    <div class="category-item">
        <span class="icon">RMS</span>
        <span>RMS data (candidates, interviews)</span>
    </div>
    <div class="category-item">
        <span class="icon">DOC</span>
        <span>Internal Edify documents</span>
    </div>
</div>
<strong>Example questions:</strong>
<ul>
    <li>list out all the learners</li>
    <li>how many leads are there in crm</li>
    <li>list out all campaigns</li>
    <li>What does the onboarding document say about batch creation?</li>
</ul>
<div class="note-box">
    <strong>Note:</strong> This assistant does not answer general knowledge questions.
</div>
    `.trim();
    
    addSystemMessage(guideContent);
}

function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message message-system';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = content;
    
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Simple markdown to HTML converter
function markdownToHtml(text) {
    if (!text) return '';
    
    // Split into lines for processing
    const lines = text.split('\n');
    const processedLines = [];
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Check if line is a numbered list item (starts with number followed by period)
        const listMatch = line.match(/^(\d+)\.\s+(.+)$/);
        
        if (listMatch) {
            if (!inList) {
                processedLines.push('<ol>');
                inList = true;
            }
            // Process the content (handle bold, etc.)
            let content = listMatch[2];
            // Convert bold text: **text**
            content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            // Escape HTML but preserve <strong> tags
            content = escapeHtmlPreserveTags(content);
            processedLines.push(`<li>${content}</li>`);
        } else {
            if (inList) {
                processedLines.push('</ol>');
                inList = false;
            }
            
            const trimmedLine = line.trim();
            if (trimmedLine) {
                // Process bold text first
                let processedLine = trimmedLine.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                // Escape HTML but preserve <strong> tags
                processedLine = escapeHtmlPreserveTags(processedLine);
                processedLines.push(`<p>${processedLine}</p>`);
            } else if (i < lines.length - 1) {
                // Empty line between content - add spacing
                processedLines.push('<br>');
            }
        }
    }
    
    // Close any open list
    if (inList) {
        processedLines.push('</ol>');
    }
    
    return processedLines.join('');
}

// Escape HTML to prevent XSS but preserve allowed tags like <strong>
function escapeHtmlPreserveTags(text) {
    // Split text into parts: HTML tags and plain text
    const parts = [];
    let lastIndex = 0;
    const tagRegex = /<strong>(.+?)<\/strong>/g;
    let match;
    
    while ((match = tagRegex.exec(text)) !== null) {
        // Add text before the tag (escaped)
        if (match.index > lastIndex) {
            parts.push(escapeHtml(text.substring(lastIndex, match.index)));
        }
        // Add the tag with escaped content
        parts.push(`<strong>${escapeHtml(match[1])}</strong>`);
        lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text (escaped)
    if (lastIndex < text.length) {
        parts.push(escapeHtml(text.substring(lastIndex)));
    }
    
    return parts.length > 0 ? parts.join('') : escapeHtml(text);
}

// Simple HTML escape
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message message-${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // For assistant messages, render markdown; for user messages, use plain text
    if (role === 'assistant') {
        messageContent.innerHTML = markdownToHtml(content);
    } else {
        messageContent.textContent = content;
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


// Allow Enter key to send (but Shift+Enter for new line)
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

