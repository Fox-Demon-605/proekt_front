class WeatherChatBot {
    constructor() {
        // Используем Vercel URL вместо localhost
        this.apiBaseUrl = 'https://proekt-front.vercel.app/';
        // Для локальной разработки
        // this.apiBaseUrl = 'http://localhost:8000';
        
        this.sessionId = null;
        this.isTyping = false;
        
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeSession();
    }
    
    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearChatButton = document.getElementById('clearChat');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.tipButtons = document.querySelectorAll('.tip-btn');
    }
    
    initializeEventListeners() {
        // Отправка сообщения по клику
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Отправка сообщения по Enter
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Очистка чата
        this.clearChatButton.addEventListener('click', () => this.clearChat());
        
        // Быстрые вопросы
        this.tipButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const text = e.target.getAttribute('data-text');
                this.messageInput.value = text;
                this.sendMessage();
            });
        });
        
        // Счетчик символов
        this.messageInput.addEventListener('input', () => this.updateCharCounter());
    }
    
    async initializeSession() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat/session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                console.log('Session initialized:', this.sessionId);
                
                // Загружаем историю, если есть
                await this.loadHistory();
            } else {
                this.showError('Не удалось создать сессию чата');
            }
        } catch (error) {
            console.error('Error initializing session:', error);
            this.showError('Ошибка подключения к серверу');
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message) {
            return;
        }
        
        // Добавляем сообщение пользователя в чат
        this.addMessageToChat(message, 'user');
        
        // Очищаем поле ввода
        this.messageInput.value = '';
        this.updateCharCounter();
        
        // Показываем индикатор печати
        this.showTypingIndicator();
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: message,
                    session_id: this.sessionId
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Скрываем индикатор печати
                this.hideTypingIndicator();
                
                // Добавляем ответ бота с задержкой для реалистичности
                setTimeout(() => {
                    this.addMessageToChat(data.message.content, 'bot');
                }, 500);
                
            } else {
                throw new Error('Ошибка отправки сообщения');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.showError('Не удалось отправить сообщение. Попробуйте еще раз.');
        }
    }
    
    async loadHistory() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat/history/${this.sessionId}`);
            
            if (response.ok) {
                const data = await response.json();
                
                // Очищаем чат, кроме первого сообщения
                this.clearChat(true);
                
                // Добавляем сообщения из истории
                data.messages.forEach((msg, index) => {
                    if (index > 0) { // Пропускаем первое приветственное сообщение
                        setTimeout(() => {
                            this this.addMessageToChat(msg.content, msg.sender);
                        }, index * 100);
                    }
                });
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }
    
    addMessageToChat(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const senderName = sender === 'user' ? 'Вы' : 'Погодный Бот';
        const senderIcon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-sender">
                    <i class="${senderIcon}"></i> ${senderName}
                </div>
                <div class="message-text">${this.escapeHtml(content)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        this.chatMessages.appendChild.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Анимация появления
        messageDiv.style.animation = 'fadeIn 0.3s ease';
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        this.typingIndicator.style.display = 'none';
    }
    
    clearChat(preserveWelcome = false) {
        if (preserveWelcome) {
            // Оставляем только первое сообщение (приветствие бота)
            const messages = this.chatMessages.querySelectorAll('.message');
            messages.forEach((msg, index) => {
                if (index > 0) {
                    msg.remove();
                }
            });
        } else {
            // Полностью очищаем чат
            this.chatMessages.innerHTML = `
                <div class="message bot">
                    <div class="message-content">
                        <div class="message-sender">
                            <i class="fas fa-robot"></i> Погодный Бот
                        </div>
                        <div class="message-text">
                            Привет! Я бот погоды. Спросите о погоде в любом городе России!
                        </div>
                        <div class="message-time">Только что</div>
                    </div>
                </div>
            `;
        }
        
        // Создаем новую сессию
        this.initializeSession();
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        `;
        
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
        
        // Удаляем сообщение об ошибке через 5 секунд
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    updateCharCounter() {
        const maxLength = 500;
        const currentLength = this.messageInput.value.length;
        const counter = document.querySelector('.char-counter') || this.createCharCounter();
        
        counter.textContent = `${currentLength}/${maxLength}`;
        
        counter.classList.remove('warning', 'error');
        
        if (currentLength > maxLength * 0.8) {
            counter.classList.add('warning');
        }
        
        if (currentLength > maxLength) {
            counter.classList.add('error');
            this.sendButton.disabled = true;
        } else {
            this.sendButton.disabled = false;
        }
    }
    
    createCharCounter() {
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        this.messageInput.parentNode.appendChild(counter);
        return counter;
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.chatBot = new WeatherChatBot();
    
    // Фокус на поле ввода
    document.getElementById('messageInput').focus();
});
