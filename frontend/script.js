// Конфигурация API
const API_BASE_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws';

// Глобальные переменные
let currentUser = null;
let currentSession = null;
let ws = null;
let messageQueue = [];
let isTyping = false;

// DOM элементы
const authContainer = document.getElementById('authContainer');
const chatContainer = document.getElementById('chatContainer');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const chatMessages = document.getElementById('chatMessages');
const typingIndicator = document.getElementById('typingIndicator');
const charCounter = document.getElementById('charCounter');
const userEmail = document.getElementById('userEmail');
const sessionId = document.getElementById('sessionId');
const logoutBtn = document.getElementById('logoutBtn');
const newSessionBtn = document.getElementById('newSessionBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const notificationsToggle = document.getElementById('notificationsToggle');
const themeButtons = document.querySelectorAll('.theme-btn');

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkAuth();
    loadSettings();
    initAutoResize();
});

// Инициализация обработчиков событий
function initEventListeners() {
    // Авторизация
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => switchAuthTab(tab.dataset.tab));
    });
    
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    
    // Чат
    messageForm.addEventListener('submit', handleMessageSubmit);
    messageInput.addEventListener('input', updateCharCounter);
    messageInput.addEventListener('keydown', handleKeyDown);
    
    // Кнопки
    logoutBtn.addEventListener('click', handleLogout);
    newSessionBtn.addEventListener('click', createNewSession);
    clearChatBtn.addEventListener('click', clearChat);
    settingsBtn.addEventListener('click', () => showModal(settingsModal));
    closeSettings.addEventListener('click', () => hideModal(settingsModal));
    
    // Настройки
    notificationsToggle.addEventListener('change', saveSettings);
    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTheme(btn.dataset.theme));
    });
    
    // Клик вне модального окна
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            hideModal(settingsModal);
        }
    });
}

// Проверка авторизации
async function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            showChat();
            initWebSocket();
            loadSession();
        } else {
            localStorage.removeItem('token');
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
    }
}

// Переключение вкладок авторизации
function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`${tab}Form`).).classList.add('active');
}

// Обработка входа
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorElement = document.getElementById('loginError');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('token', data.access_token);
            currentUser = data.user;
            showNotification('Успешный вход!', 'success');
            showChat();
            initWebSocket();
            loadSession();
        } else {
            showError(errorElement, data.detail || 'Ошибка входа');
        }
    } catch (error) {
        showError(errorElement, 'Ошибка соединения');
    }
}

// Обработка регистрации
async function handleRegister(e) {
    e.preventDefault();
    
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirm = document.getElementById('registerConfirm').value;
    const errorElement = document.getElementById('registerError');
    
    if (password !== confirm) {
        showError(errorElement, 'Пароли не совпадают');
        return;
    }
    
    if (password.length < 6) {
        showError(errorElement, 'Пароль должен быть не менее 6 символов');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Регистрация успешна!', 'success');
            switchAuthTab('login');
            document.getElementById('loginEmail').value = email;
            document.getElementById('loginPassword').value = '';
        } else {
            showError(errorElement, data.detail || 'Ошибка регистрации');
        }
    } catch (error) {
        showError(errorElement, 'Ошибка соединения');
    }
}

// Показать чат
function showChat() {
    authContainer.style.display = 'none';
    chatContainer.style.display = 'flex';
    userEmail.textContent = currentUser.email;
    messageInput.focus();
}

// Инициализация WebSocket
function initWebSocket() {
    const token = localStorage.getItem('token');
    ws = new WebSocket(`${WS_URL}?token=${token}`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        processMessageQueue();
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        setTimeout(initWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Обработка сообщений WebSocket
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'session_created':
            currentSession = data.session;
            sessionId.textContent = `#${data.session.id.toString().padStart(4, '0')}`;
            break;
            
        case 'bot_typing':
            showTypingIndicator();
            break;
            
        case 'bot_response':
            hideTypingIndicator();
            addMessage(data.message, 'bot');
            break;
            
        case 'error':
            showNotification(data.message, 'error');
            break;
    }
}

// Загрузка сессии
async function loadSession() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/sessions/current`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const session = await response.json();
            currentSession = session;
            sessionId.textContent = `#${session.id.toString().padStart(4, '0')}`;
            loadMessages(session.id);
        }
    } catch (error) {
        console.error('Failed to load session:', error);
    }
}

// Загрузка сообщений
async function loadMessages(sessionId) {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const messages = await response.json();
            messages.forEach(msg => {
                addMessage(msg, msg.sender === 'user' ? 'user' : 'bot', false);
            });
            scrollToBottom();
        }
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

// Обработка отправки сообщения
async function handleMessageSubmit(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || isTyping) return;
    
    // Добавляем сообщение пользователя
    addMessage(message, 'user');
    messageInput.value = '';
    updateCharCounter();
    scrollToBottom();
    
    // Отправляем через WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'user_message',
            message: message,
            session_id: currentSession?.id
        }));
        showTypingIndicator();
    } else {
        // Если WebSocket не готов, добавляем в очередь
        messageQueue.push(message);
        showNotification('Соединение восстанавливается...', 'warning');
    }
}

// Добавление сообщения в чат
function addMessage(text, sender, animate = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender} ${animate ? 'animate' : ''}`;
    
    const time = new Date().toLocaleTimeString('ru-RU', {
        hour hour: '2-digit',
        minute: '2-digit'
    });
    
    const avatarIcon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
    const senderName = sender === 'user' ? 'Вы' : 'AI Assistant';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="${avatarIcon}"></i>
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${senderName}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${formatMessage(text)}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    if (animate) {
        messageDiv.style.animation = 'slideIn 0.3s ease';
    }
    
    scrollToBottom();
}

// Форматирование сообщения
function formatMessage(text) {
    // Заменяем переносы строк на <br>
    text = text.replace(/\n/g, '<br>');
    
    // Обработка ссылок
    text = text.replace(
        /(https?:\/\/[^\s]+)/g,
        '<a href="\$1" target="_blank" rel="noopener noreferrer">\$1</a>'
    );
    
    // Обработка кода (простой вариант)
    text = text.replace(/`([^`]+)`/g, '<code>\$1</code>');
    
    return text;
}

// Показать индикатор печати
function showTypingIndicator() {
    isTyping = true;
    typingIndicator.style.display = 'flex';
    scrollToBottom();
}

// Скрыть индикатор печати
function hideTypingIndicator() {
    isTyping = false;
    typingIndicator.style.display = 'none';
}

// Обработка клавиш
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (messageInput.value.trim()) {
            handleMessageSubmit(e);
        }
    }
    
    // Автоматическое изменение высоты textarea
    if (e.key === 'Enter' && e.shiftKey) {
        setTimeout(() => {
            messageInput.style.height = 'auto';
            messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
        }, 0);
    }
}

// Обновление счетчика символов
function updateCharCounter() {
    const length = messageInput.value.length;
    charCounter.textContent = `${length}/1000`;
    
    if (length > 900) {
        charCounter.style.color = 'var(--warning-color)';
    } else if (length > 1000) {
        charCounter.style.color = 'var(--error-color)';
    } else {
        charCounter.style.color = 'var(--text-muted)';
    }
}

// Автоматическое изменение размера textarea
function initAutoResize() {
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    });
}

// Создание новой сессии
async function createNewSession() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/sessions/new`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const session = await response.json();
            currentSession = session;
            sessionId.textContent = `#${session.id.toString().padStart(4, '0')}`;
            
            // Очищаем чат
            chatMessages.innerHTML = `
                <div class="message bot welcome">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-header">
                            <span class="message-sender">AI Assistant</span>
                            <span class="message-time">Только что</span>
                        </div>
                        <div class="message-text">
                            <h3>✨ Новая сессия создана!</h3>
                            <p>Чем могу помочь?</p>
                        </div>
                    </div>
                </div>
            `;
            
            showNotification('Новая сессия создана', 'success');
        }
    } catch (error) {
        showNotification('Ошибка создания сессии', 'error');
    }
}

// Очистка чата
function clearChat() {
    if (confirm('Очистить историю текущей сессии?')) {
        chatMessages.innerHTML = `
            <div class="message bot welcome">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-sender">AI Assistant</span>
                        <span class="message-time">Только что</span>
                    </div>
                    <div class="message-text">
                        <h3>🧹 Чат очищен</h3>
                        <p>История сообщений удалена. Чем могу помочь?</p>
                    </div>
                </div>
            </div>
        `;
        showNotification('Чат очищен', 'info');
    }
}

// Выход из системы
function handleLogout() {
    if (confirm('Выйти из системы?')) {
        localStorage.removeItem('token');
        currentUser = null;
        currentSession = null;
        
        if (ws) {
            ws.close();
        }
        
        chatContainer.style.display = 'none';
        authContainer.style.display = 'block';
        
        // Сброс форм
        loginForm.reset();
        registerForm.reset();
        switchAuthTab('login');
        
        showNotification('Вы вышли из системы', 'info');
    }
}

// Прокрутка вниз
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Показать уведомление
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Показать ошибку
function showError(element, message) {
    element.textContent = message;
    element.style.display = 'block';
    
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

// Показать модальное окно
function showModal(modal) {
    modal.classList.add('show');
}

// Скрыть модальное окно
function hideModal(modal) {
    modal.classList.remove('show');
}

// Загрузка настроек
function loadSettings() {
    const theme = localStorage.getItem('theme') || 'dark';
    const notifications = localStorage.getItem('notifications') !== 'false';
    
    document.documentElement.setAttribute('data-theme', theme);
    notificationsToggle.checked = notifications;
    
    themeButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
    });
}

// Сохранение настроек
function saveSettings() {
    localStorage.setItem('notifications', notificationsToggle.checked);
    showNotification('Настройки сохранены', 'success');
}

// Переключение темы
function switchTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    themeButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
    });
}

// Обработка очереди сообщений
function processMessageQueue() {
    while (messageQueue.length > 0 && ws && ws.readyState === WebSocket.OPEN) {
        const message = messageQueue.shift();
        ws.send(JSON.stringify({
            type: 'user_message',
            message: message,
            session_id: currentSession?.id
        }));
    }
}

// Обработка ошибок
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    showNotification('Произошла ошибка', 'error');
});

// Обработка offline/online
window.addEventListener('offline', () => {
    showNotification('Отсутствует интернет-соединение', 'warning');
});

window.addEventListener('online', () => {
    showNotification('Соединение восстановлено', 'success');
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        initWebSocket();
    }
});
