// Основные константы и переменные
const API_BASE_URL = 'http://localhost:5000/api';
let currentUser = null;
let authModal = null;
let chatWidget = null;
let currentBook = null;
let currentList = 'reading';

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

async function initApp() {
    // Проверка авторизации
    await checkAuth();
    
    // Инициализация компонентов
    initAuthModal();
    initNavigation();
    initSearch();
    initFilters();
    initBookGrid();
    initLists();
    initChatBot();
    initNotifications();
    
    // Загрузка данных
    loadBooks();
    loadUserLists();
    loadStats();
    
    // Обработчики событий
    setupEventListeners();
}

// ==================== АВТОРИЗАЦИЯ ====================

// Проверка авторизации
async function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        showAuthModal();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            updateUIForAuth(true);
        } else {
            localStorage.removeItem('token');
            showAuthModal();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showAuthModal();
    }
}

// Инициализация модалки авторизации
function initAuthModal() {
    authModal = document.querySelector('.auth-modal');
    if (!authModal) return;
    
    // Переключение между вкладками
    const tabs = document.querySelectorAll('.auth-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabType = tab.dataset.tab;
            switchAuthTab(tabType);
        });
    });
    
    // Форма входа
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleLogin();
    });
    
    // Форма регистрации
    const registerForm = document.getElementById('registerForm');
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleRegister();
    });
}

// Переключение вкладок авторизации
function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === tab);
    });
    
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.toggle('active', form.id === `${tab}Form`);
    });
    
    document.querySelector('.auth-error').style.display = 'none';
}

// Обработка входа
async function handleLogin() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorElement = document.querySelector('.auth-error');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('token', data.token);
            currentUser = data.user;
            updateUIForAuth(true);
            hideAuthModal();
            showNotification('Успешный вход!', 'success');
            loadUserData();
        } else {
            errorElement.textContent = data.message || 'Ошибка входа';
            errorElement.style.display = 'block';
        }
    } catch (error) {
        errorElement.textContent = 'Ошибка соединения';
        errorElement.style.display = 'block';
    }
}

// Обработка регистрации
async function handleRegister() {
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const errorElement = document.querySelector('.auth-error');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('token', data.token);
            currentUser = data.user;
            updateUIForAuth(true);
            hideAuthModal();
            showNotification('Регистрация успешна!', 'success');
            loadUserData();
        } else {
            errorElement.textContent = data.message || 'Ошибка регистрации';
            errorElement.style.display = 'block';
        }
    } catch (error) {
        errorElement.textContent = 'Ошибка соединения';
        errorElement.style.display = 'block';
    }
}

// Выход из системы
function handleLogout() {
    localStorage.removeItem('token');
    currentUser = null;
    updateUIForAuth(false);
    showAuthModal();
    showNotification('Вы вышли из системы', 'info');
}

// Обновление UI при авторизации
function updateUIForAuth(isAuthenticated) {
    const authElements = document.querySelectorAll('[data-auth]');
    const guestElements = document.querySelectorAll('[data-guest]');
    
    authElements.forEach(el => {
        el.style.display = isAuthenticated ? 'flex' : 'none';
    });
    
    guestElements.forEach(el => {
        el.style.display = isAuthenticated ? 'none' : 'flex';
    });
    
    if (isAuthenticated && currentUser) {
        document.querySelector('.user-name').textContent = currentUser.username;
    }
}

// Показать/скрыть модалку авторизации
function showAuthModal() {
    if (authModal) {
        authModal.style.display = 'flex';
        document.getElementById('loginEmail').focus();
    }
}

function hideAuthModal() {
    if (authModal) {
        authModal.style.display = 'none';
    }
}

// ==================== КНИГИ ====================

// Загрузка книг
async function loadBooks(filters = {}) {
    const booksGrid = document.querySelector('.books-grid');
    if (!booksGrid) return;
    
    booksGrid.innerHTML = '<div class="loader"></div>';
    
    try {
        const queryParams = new URLSearchParams(filters).toString();
        const response = await fetch(`${API_BASE_URL}/books?${queryParams}`);
        const books = await response.json();
        
        renderBooks(books);
    } catch (error) {
        console.error('Failed to load books:', error);
        booksGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Ошибка загрузки</h3>
                <p>Не удалось загрузить книги</p>
                <button class="btn btn-primary" onclick="loadBooks()">Повторить</button>
            </div>
        `;
    }
}

// Отображение книг
function renderBooks(books) {
    const booksGrid = document.querySelector('.books-grid');
    if (!booksGrid) return;
    
    if (books.length === 0) {
        booksGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book"></i>
                <h3>Книги не найдены</h3>
                <p>Попробуйте изменить фильтры</p>
            </div>
        `;
        return;
    }
    
    booksGrid.innerHTML = books.map(book => `
        <div class="book-card" data-book-id="${book.id}">
            <div class="book-cover">
                ${book.cover_url ? 
                    `<img src="${book.cover_url}" alt="${book.title}">` : 
                    `<i class="fas fa-book"></i>`
                }
            </div>
            <div class="book-info">
                <h3 class="book-title">${book.title}</h3>
                <p class="book-author">${book.author}</p>
                <div class="book-meta">
                    <span class="book-genre">${book.genre}</span>
                    <span class="book-rating">
                        <i class="fas fa-star"></i> ${book.rating || '4.5'}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
    
    // Добавляем обработчики кликов
    document.querySelectorAll('.book-card').forEach(card => {
        card.addEventListener('click', () => {
            const bookId = card.dataset.bookId;
            openBookPage(bookId);
        });
    });
}

// Открытие страницы книги
async function openBookPage(bookId) {
    try {
        const response = await fetch(`${API_BASE_URL}/books/${bookId}`);
        const book = await response.json();
        
        currentBook = book;
        renderBookPage(book);
        
        // Обновляем URL
        history.pushState({ bookId }, '', `/book/${bookId}`);
        
        // Показываем страницу книги
        document.querySelector('.library-section').style.display = 'none';
        document.querySelector('.book-page').style.display = 'block';
    } catch (error) {
        console.error('Failed to load book:', error);
        showNotification('Не удалось загрузить книгу', 'error');
    }
}

// Отображение страницы книги книги
function renderBookPage(book) {
    const bookPage = document.querySelector('.book-page');
    if (!bookPage) return;
    
    bookPage.innerHTML = `
        <div class="book-page-header">
            <button class="btn btn-back" onclick="goBackToLibrary()">
                <i class="fas fa-arrow-left"></i> Назад
            </button>
            <div class="book-actions">
                <button class="btn btn-outline" onclick="addToReadingList(${book.id})">
                    <i class="fas fa-plus"></i> В список
                </button>
                <button class="btn btn-primary" onclick="startReading(${book.id})">
                    <i class="fas fa-play"></i> Читать
                </button>
            </div>
        </div>
        
        <div class="book-page-content">
            <div class="book-cover-large">
                ${book.cover_url ? 
                    `<img src="${book.cover_url}" alt="${book.title}">` : 
                    `<div class="book-cover"><i class="fas fa-book"></i></div>`
                }
                <div class="book-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${book.progress || 0}%"></div>
                    </div>
                    <span>${book.progress || 0}% прочитано</span>
                </div>
            </div>
            
            <div class="book-details">
                <h1>${book.title}</h1>
                <p class="book-author">${book.author}</p>
                
                <div class="book-genres">
                    ${book.genres ? book.genres.map(genre => `
                        <span class="genre-tag">${genre}</span>
                    `).join('') : ''}
                </div>
                
                <div class="book-description">
                    <h3>Описание</h3>
                    <p>${book.description || 'Описание отсутствует'}</p>
                </div>
                
                <div class="book-meta">
                    <div class="meta-item">
                        <i class="fas fa-calendar"></i>
                        <span>Год: ${book.year || 'Не указа указан'}</span>
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-file-alt"></i>
                        <span>Страниц: ${book.pages || 'Не указано'}</span>
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-star"></i>
                        <span>Рейтинг: ${book.rating || 'Нет оценок'}</span>
                    </div>
                </div>
                
                <div class="reading-controls">
                    <h3><i class="fas fa-book-open"></i> Начать чтение</h3>
                    <div class="chapter-selector">
                        <label for="chapterSelect">Глава:</label>
                        <select id="chapterSelect">
                            ${book.chapters ? book.chapters.map((chapter, index) => `
                                <option value="${index}">${chapter.title}</option>
                            `).join('') : '<option>Глава 1</option>'}
                        </select>
                    </div>
                    <button class="btn btn-large btn-primary" onclick="startReading(${book.id})">
                        <i class="fas fa-play"></i> Начать чтение
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Возврат в библиотеку
function goBackToLibrary() {
    document.querySelector('.library-section').style.display = 'block';
    document.querySelector('.book-page').style.display = 'none';
    history.back();
}

// ==================== СПИСКИ ====================

// Загрузка списков пользователя
async function loadUserLists() {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/user/lists`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const lists = await response.json();
            renderLists(lists);
        }
    } catch (error) {
        console.error('Failed to load lists:', error);
    }
}

// Отображение списков
function renderLists(lists) {
    const listsContent = document.querySelector('.lists-content');
    if (!listsContent) return;
    
    // Обновляем активную вкладку
    document.querySelectorAll('.list-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const listType = tab.dataset.list;
            switchListTab(listType);
        });
    });
    
    // Рендерим содержимое для каждого списка
    const listTypes = ['reading', 'planned', 'completed', 'favorites'];
    
    listTypes.forEach(listType => {
        const panel = document.getElementById(`${listType}List`);
        if (!panel) return;
        
        const listItems = lists[listType] || [];
        
        if (listItems.length === 0) {
            panel.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-book"></i>
                    <h3>Список пуст</h3>
                    <p>Добавьте книги в этот список</p>
                </div>
            `;
        } else {
            panel.innerHTML = listItems.map(book => `
                <div class="list-item" data-book-id="${book.id}">
                    ${book.cover_url ? 
                        `<img src="${book.cover_url}" class="list-item-cover" alt="${book.title}">` :
                        `<div class="list-item-cover"><i class="fas fa-book"></i></div>`
                    }
                    <div class="list-item-info">
                        <div class="list-item-title">${book.title}</div>
                        <div class="list-item-author">${book.author}</div>
                        ${listType === 'reading' ? `
                            <div class="list-item-progress">${book.progress || 0}% прочитано</div>
                        ` : ''}
                    </div>
                    <button class="btn btn-send" onclick="removeFromList(${book.id}, '${listType}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `).join('');
            
            // Добавляем обработчики кликов
            panel.querySelectorAll('.list-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (!e.target.closest('.btn')) {
                        const bookId = item.dataset.bookId;
                        openBookPage(bookId);
                    }
                });
            });
        }
    });
}

// Переключение вкладок списков
function switchListTab(listType) {
    currentList = listType;
    
    document.querySelectorAll('.list-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.list === listType);
    });
    
    document.querySelectorAll('.list-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `${listType}List`);
    });
}

// Добавление книги в список
async function addToReadingList(bookId, listType = 'reading') {
    if (!currentUser) {
        showAuthModal();
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/user/lists/${listType}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ bookId })
        });
        
        if (response.ok) {
            showNotification('Книга добавлена в список', 'success');
            loadUserLists();
        }
    } catch (error) {
        console.error('Failed to add to list:', error);
        showNotification('Ошибка добавления', 'error');
    }
}

// Удаление книги из списка
async function removeFromList(bookId, listType) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/user/lists/${listType}/${bookId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            showNotification('Книга удалена из списка', 'success');
            loadUserLists();
        }
    } catch (error) {
        console.error('Failed to remove from list:', error);
        showNotification('Ошибка удаления', 'error');
    }
}

// ==================== ПОИСК И ФИЛЬТРЫ ====================

// Инициализация поиска
function initSearch() {
    const searchInput = document.querySelector('.search-box input');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(e.target.value);
        }, 500);
    });
}

// Выполнение поиска
async function performSearch(query) {
    if (query.length < 2) {
        loadBooks();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/books/search?q=${encodeURIComponent(query)}`);
        const books = await response.json();
        renderBooks(books);
    } catch (error) {
        console.error('Search failed:', error);
    }
}

// Инициализация фильтров
function initFilters() {
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(selectselect => {
        select.addEventListener('change', () => {
            applyFilters();
        });
    });
}

// Применение фильтров
function applyFilters() {
    const filters = {};
    
    document.querySelectorAll('.filter-select').forEach(select => {
        if (select.value) {
            filters[select.name] = select.value;
        }
    });
    
    loadBooks(filters);
}

// ==================== ЧАТ-БОТ ====================

// Инициализация чат-бота
function initChatBot() {
    chatWidget = document.querySelector('.chat-widget');
    const chatToggle = document.querySelector('.chat-toggle');
    const chatClose = document.querySelector('.chat-close');
    const sendButton = document.querySelector('.btn-send');
    const chatInput = document.querySelector('.chat-input-area input');
    const quickSuggestions = document.querySelectorAll('.quick-suggestion');
    
    if (!chatWidget || !chatToggle) return;
    
    // Переключение видимости чата
    chatToggle.addEventListener('click', () => {
        chatWidget.classList.toggle('active');
        if (chatWidget.classList.contains('active')) {
            chatInput.focus();
        }
    });
    
    // Закрытие чата
    if (chatClose) {
        chatClose.addEventListener('click', () => {
            chatWidget.classList.remove('active');
        });
    }
    
    // Отправка сообщения
    if (sendButton && chatInput) {
        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (message) {
                addUserMessage(message);
                chatInput.value = '';
                processBotResponse(message);
            }
        };
        
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Быстрые предложения
    quickSuggestions.forEach(button => {
        button.addEventListener('click', () => {
            const message = button.textContent;
            addUserMessage(message);
            processBotResponse(message);
        });
    });
}

// Добавление сообщения пользователя
function addUserMessage(text) {
    const messagesContainer = document.querySelector('.chat-messages');
    if (!messagesContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message user';
    messageElement.innerHTML = `
        <div class="message-text">${escapeHtml(text)}</div>
        <div class="message-time">${formatTime(new Date())}</div>
    `;
    
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Показываем индикатор набора
    showTypingIndicator();
}

// Добавление сообщения бота
function addBotMessage(text) {
    const messagesContainer = document.querySelector('.chat-messages');
    if (!messagesContainer) return;
    
    // Убираем индикатор набора
    hideTypingIndicator();
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot';
    messageElement.innerHTML = `
        <div class="message-text">${escapeHtml(text)}</div>
        <div class="message-time">${formatTime(new Date())}</div>
    `;
    
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Показать индикатор набора
function showTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'flex';
    }
}

// Скрыть индикатор набора
function hideTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

// Обработка ответа бота
async function processBotResponse(userMessage) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                message: userMessage,
                userId: currentUser?.id
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            setTimeout(() => {
                addBotMessage(data.response);
            }, 1000);
        } else {
            setTimeout(() => {
                addBotMessage('Извините, произошла ошибка. Попробуйте позже.');
            }, 1000);
        }
    } catch (error) {
        console.error('Chat error:', error);
        setTimeout(() => {
            addBotMessage('Не могу подключиться к серверу. Проверьте соединение.');
        }, 1000);
    }
}

// ==================== УВЕДОМЛЕНИЯ ====================

// Инициализация уведомлений
function initNotifications() {
    // Периодическая проверка новых уведомлений
    if (currentUser) {
        setInterval(checkNotifications,  30000); // Каждые 30 секунд
    }
}

// Проверка уведомлений
async function checkNotifications() {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/notifications`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const notifications = await response.json();
            notifications.forEach(notification => {
                showNotification(notification.message, notification.type);
            });
        }
    } catch (error) {
        console.error('Failed to check notifications:', error);
    }
}

// Показать уведомление
function showNotification(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type] || 'fa-info-circle'}"></i>
        <div class="toast-content">
            <div class="toast-title">${type === 'success' ? 'Успешно' : type === 'error' ? 'Ошибка' : 'Информация'}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

// ==================== СТАТИСТИКА ====================

// Загрузка статистики
async function loadStats() {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/user/stats`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            renderStats(stats);
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Отображение статистики
function renderStats(stats) {
    const statsContainer = document.querySelector('.stats');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = `
        <div class="stat-item">
            <span class="stat-number">${stats.booksRead || 0}</span>
            <span class="stat-label">Прочитано</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">${stats.pagesRead || 0}</span>
            <span class="stat-label">Страниц</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">${stats.readingTime || 0}</span>
            <span class="stat-label">Часов</span>
        </div>
    `;
}

// ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Форматирование времени
function formatTime(date) {
    return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Инициализация навигации
function initNavigation() {
    // Обработка кликов по навигации
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            navigateTo(page);
        });
    });
    
    // Кнопка выхода
    const logoutBtn = document.querySelector('.btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}

// Навигация по страницам
function navigateTo(page) {
    switch (page) {
        case 'library':
            goBackToLibrary();
            break;
        case 'profile':
            // TODO: Реализовать страницу профиля
            showNotification('Страница профиля в разработке', 'info');
            break;
        case 'settings':
            // TODO: Реализовать настройки
            showNotification('Настройки в разработке', 'info');
            break;
    }
}

// Инициализация сетки книг
function initBookGrid() {
    // Уже реализовано в renderBooks
}

// Инициализация списков
function initLists() {
    // Уже реализовано в renderLists
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработка истории браузера
    window.addEventListener('popstate', (event) => {
        if (event.state && event.state.bookId) {
            openBookPage(event.state.bookId);
        } else {
            goBackToLibrary();
        }
    });
    
    // Закрытие модалки по клику вне ее
    if (authModal) {
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) {
                hideAuthModal();
            }
        });
    }
    
    // Глобальные горячие клавиши
    document.addEventListener('keydown', (e) => {
        // ESC - закрыть модалки
        if (e.key === 'Escape') {
            if (authModal && authModal.style.display === 'flex') {
                hideAuthModal();
            }
            if (chatWidget && chatWidget.classList.contains('active')) {
                chatWidget.classList.remove('active');
            }
        }
        
        // Ctrl+K - поиск
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-box input');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}

// Загрузка данных пользователя
async function loadUserData() {
    await Promise.all([
        loadUserLists(),
        loadStats(),
        checkNotifications()
    ]);
}

// Начать чтение книги
async function startReading(bookId) {
    if (!currentUser) {
        showAuthModal();
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        const chapterSelect = document.getElementById('chapterSelect');
        const chapter = chapterSelect ? chapterSelect.value : 0;
        
        const response = await fetch(`${API_BASE_URL}/reading/start`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bookId,
                               chapter: parseInt(chapter)
            })
        });
        
        if (response.ok) {
            showNotification('Чтение начато', 'success');
            // TODO: Открыть читалку
            window.open(`/reader/${bookId}?chapter=${chapter}`, '_blank');
        }
    } catch (error) {
        console.error('Failed to start reading:', error);
        showNotification('Ошибка начала чтения', 'error');
    }
}

// Экспорт функций для глобального использования
window.handleLogout = handleLogout;
window.addToReadingList = addToReadingList;
window.removeFromList = removeFromList;
window.startReading = startReading;
window.goBackToLibrary = goBackToLibrary;
window.showNotification = showNotification;

// ==================== ЧИТАЛКА КНИГ ====================

// Инициализация читалки
function initReader() {
    const readerContainer = document.querySelector('.reader-container');
    if (!readerContainer) return;
    
    setupReaderControls();
    loadReaderSettings();
    setupReaderEvents();
}

// Настройка элементов управления читалкой
function setupReaderControls() {
    // Кнопки навигации
    document.querySelectorAll('.reader-nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.currentTarget.dataset.action;
            handleReaderAction(action);
        });
    });
    
    // Настройки отображения
    document.querySelectorAll('.reader-setting').forEach(setting => {
        setting.addEventListener('change', (e) => {
            updateReaderSetting(e.target.name, e.target.value);
        });
    });
    
    // Закладки
    document.querySelector('.btn-bookmark').addEventListener('click', toggleBookmark);
    
    // Прогресс чтения
    const progressSlider = document.querySelector('.progress-slider');
    if (progressSlider) {
        progressSlider.addEventListener('input', (e) => {
            updateReadingProgress(e.target.value);
        });
    }
}

// Загрузка настроек читалки из localStorage
function loadReaderSettings() {
    const settings = {
        fontSize: localStorage.getItem('readerFontSize') || '16',
',
        theme: localStorage.getItem('readerTheme') || 'light',
        fontFamily: localStorage.getItem('readerFontFamily') || 'serif',
        lineHeight: localStorage.getItem('readerLineHeight') || '1.5'
    };
    
    Object.entries(settings).forEach(([key, value]) => {
        updateReaderSetting(key, value, false);
        
        // Устанавливаем значения в UI
        const input = document.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = value;
        }
    });
}

// Обновление настроек читалки
function updateReaderSetting(key, value, save = true) {
    const readerContent = document.querySelector('.reader-content');
    if (!readerContent) return;
    
    switch(key) {
        case 'fontSize':
            readerContent.style.fontSize = `${value}px`;
            break;
        case 'theme':
            document.documentElement.setAttribute('data-theme', value);
            break;
        case 'fontFamily':
            readerContent.style.fontFamily = getFontFamily(value);
            break;
        case 'lineHeight':
            readerContent.style.lineHeight = value;
            break;
    }
    
    if (save) {
        localStorage.setItem(`reader${key.charAt(0).toUpperCase() + key.slice(1)}`, value);
    }
}

// Получение семейства шрифтов
function getFontFamily(value) {
    const fonts = {
        'serif': 'Georgia, "Times New Roman", serif',
        'sans': 'Arial, Helvetica, sans-serif',
        'mono': '"Courier New", monospace',
        'modern': '"Segoe UI", Roboto, sans-serif'
    };
    return fonts[value] || fonts.serif;
}

// Обработка действий в читалке
async function handleReaderAction(action) {
    const currentChapter = get getCurrentChapter();
    
    switch(action) {
        case 'prev':
            await navigateChapter(currentChapter - 1);
            break;
        case 'next':
            await navigateChapter(currentChapter + 1);
            break;
        case 'toc':
            toggleTableOfContents();
            break;
        case 'search':
            openReaderSearch();
            break;
        case 'fullscreen':
            toggleFullscreen();
            break;
    }
}

// Навигация по главам
async function navigateChapter(chapterIndex) {
    if (chapterIndex < 0) return;
    
    try {
        const token = localStorage.getItem('token');
        const bookId = getCurrentBookId();
        
        const response = await fetch(`${API_BASE_URL}/reading/chapter/${bookId}/${chapterIndex}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const chapter = await response.json();
            renderChapter(chapter);
            updateReaderProgress(chapterIndex);
        }
    } catch (error) {
        console.error('Failed to navigate chapter:', error);
        showNotification('Ошибка загрузки главы', 'error');
    }
}

// Отображение главы
function renderChapter(chapter) {
    const readerContent = document.querySelector('.reader-content');
    if (!readerContent) return;
    
    readerContent.innerHTML = `
        <div class="chapter-header">
            <h1 class="chapter-title">${chapter.title}</h1>
            <div class="chapterchapter-meta">
                <span class="chapter-number">Глава ${chapter.number}</span>
                <span class="chapter-progress">${chapter.progress}%</span>
            </div>
        </div>
        <div class="chapter-content">
            ${chapter.content}
        </div>
    `;
    
    // Обновляем заголовок страницы
    document.title = `${chapter.title} - ${currentBook?.title || 'Чтение'}`;
    
    // Сохраняем позицию
    saveReadingPosition();
}

// Получение текущей главы
function getCurrentChapter() {
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('chapter')) || 0;
}

// Получение ID текущей книги
function getCurrentBookId() {
    const path = window.location.pathname;
    const match = path.match(/\/book\/(\d+)/);
    return match ? match[1] : null;
}

// Обновление прогресса чтения
async function updateReaderProgress(chapterIndex) {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('token');
        const bookId = getCurrentBookId();
        
        await fetch(`${API_BASE_URL}/reading/progress`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bookId,
                chapter: chapterIndex,
                progress: calculateChapterProgress()
            })
        });
    } catch (error) {
        console.error('Failed to update progress:', error);
    }
}

// Расчет прогресса главы
function calculateChapterProgress() {
    const readerContent = document.querySelector('.reader-content');
    if (!readerContent) return 0;
    
    const scrollTop = readerContent.scrollTop;
    const scrollHeight = readerContent.scrollHeight;
    const clientHeight = readerContent.clientHeight;
    
    return Math.round((scrollTop / (scrollHeight - clientHeight)) * 100);
}

// Сохранение позиции чтения
function saveReadingPosition() {
    const readerContent = document.querySelector('.reader-content');
    if (!readerContent) return;
    
    const position = readerContent.scrollTop;
    const bookId = getCurrentBookId();
    const chapter = getCurrentChapter();
    
    localStorage.setItem(`readingPosition_${bookId}_${chapter}`, position);
}

// Восстановление позиции чтения
function restoreReadingPosition() {
    const readerContent = document.querySelector('.reader-content');
    if (!readerContent) return;
    
    const bookId = getCurrentBookId();
    const chapter = getCurrentChapter();
    const position = localStorage.getItem(`readingPosition_${bookId}_${chapter}`);
    
    if (position) {
        setTimeout(() => {
            readerContent.scrollTop = parseInt(position);
        }, 100);
    }
}

// Переключение закладки
async function toggleBookmark() {
    if (!currentUser) return;
    
    const bookId = getCurrentBookId();
    const chapter = getCurrentChapter();
    const position = calculateChapterProgress();
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/bookmarks`, {
            method: 'POSTPOST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bookId,
                chapter,
                position,
                note: ''
            })
        });
        
        if (response.ok) {
            const isBookmarked = await response.json();
            updateBookmarkUI(isBookmarked);
            showNotification(isBookmarked ? 'Закладка добавлена' : 'Закладка удалена', 'success');
        }
    } catch (error) {
        console.error('Failed to toggle bookmark:', error);
        showNotification('Ошибка работы с закладкой', 'error');
    }
}

// Обновление UI закладки
function updateBookmarkUI(isBookmarked) {
    const bookmarkBtn = document.querySelector('.btn-bookmark');
    if (!bookmarkBtn) return;
    
    const icon = bookmarkBtn.querySelector('i');
    if (icon) {
        icon.className = isBookmarked ? 'fas fa-bookmark' : 'far fa-bookmark';
    }
    bookmarkBtn.classList.toggle('active', isBookmarked);
}

// Переключение оглавления
function toggleTableOfContents() {
    const tocPanel = document.querySelector('.toc-panel');
    if (tocPanel) {
        tocPanel.classList.toggle('active');
    }
}

// Открытие поиска в читалке
function openReaderSearch() {
    const searchOverlay = document.querySelector('.reader-search-overlay');
    if (searchOverlay) {
        searchOverlay.classList.add('active');
        const searchInput = searchOverlay.querySelector('input');
        if (searchInput) {
            searchInput.focus();
        }
    }
}

// Переключение полноэкранного режима
function toggleFullscreen() {
    const readerContainer = document.querySelector('.reader-container');
    if (!readerContainer) return;
    
    if (!document.fullscreenElement) {
        if (readerContainer.requestFullscreen) {
            readerContainer.requestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// Настройка событий читалки
function setupReaderEvents() {
    // Автосохранение прогресса
    const readerContent = document.querySelector('.reader-content');
    if (readerContent) {
        let saveTimeout;
        readerContent.addEventListener('scroll', () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(saveReadingPosition, 1000);
        });
    }
    
    // Горячие клавиши для читалки
    document.addEventListener('keykeydown', (e) => {
        if (!document.querySelector('.reader-container')) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                handleReaderAction('prev');
                break;
            case 'ArrowRight':
                handleReaderAction('next');
                break;
            case ' ':
                e.preventDefault();
                handleReaderAction('next');
                break;
            case 'b':
                toggleBookmark();
                break;
            case 'f':
                toggleFullscreen();
                break;
            case 'Escape':
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                }
                break;
        }
    });
    
    // Обработка изменения полноэкранного режима
    document.addEventListener('fullscreenchange', () => {
        const fullscreenBtn = document.querySelector('[data-action="fullscreen"]');
        if (fullscreenBtn) {
            const icon = fullscreenBtn.querySelector('i');
            if (icon) {
                icon.className = document.fullscreenElement ? 
                    'fas fa-compress' : 'fas fa-expand';
            }
        }
    });
}

// ==================== РЕКОМЕНДАЦИИ ====================

// Загрузка рекомендаций
async function loadRecommendations() {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/recommendations`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const recommendations = await response.json();
            renderRecommendations(recommendations);
        }
    } catch (error) {
        console.error('Failed to load recommendations:', error);
    }
}

// Отображение рекомендаций
function renderRecommendations(recommendations) {
    const container = document.querySelector('.recommendations-grid');
    if (!container) return;
    
    if (recommendations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-lightbulb"></i>
                <h3>Нет рекомендаций</h3>
                <p>Прочитайте больше книг для персонализированных рекомендаций</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = recommendations.map(book => `
        <div class="recommendation-card" data-book-id="${book.id}">
            <div class="recommendation-badge">
                <i class="fas fa-star"></i>
                Рекомендуем
            </div>
            <div class="book-cover">
                ${book.cover_url ? 
                    `<img src="${book.cover_url}" alt="${book.title}">` : 
                    `<i class="fas fa-book"></i>`
                }
            </div>
            <div class="book-info">
                <h4 class="book-title">${book.title}</h4>
                <p class="book-author">${book.author}</p>
                <div class="recommendation-reason">
                    <i class="fas fa-check-circle"></i>
                    ${book.reason || 'На основе вашего чтения'}
                </div>
                <button class="btn btn-sm btn-primary" onclick="addToReadingList(${book.id})">
                    Добавить в список
                </button>
            </div>
        </div>
    `).join('');
    
    // Добавляем обработчики кликов
    container.querySelectorAll('.recommendation-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.btn')) {
                const bookId = card.dataset.bookId;
                openBookPage(bookId);
            }
        });
    });
}

// ==================== ЦИТАТЫ И ЗАМЕТКИ ====================

// Инициализация системы цитат
function initQuotesSystem() {
    const highlightBtn = document.querySelector('.btn-highlight');
    if (highlightBtn) {
        highlightBtn.addEventListener('click', handleTextHighlight);
    }
    
    setupQuoteSelection();
}

// Обработка выделения текста
function handleTextHighlight() {
    const selection = window.getSelection();
    if (selection.toString().trim().length < 10) {
        showNotification('Выделите больше текста для цитаты', 'info');
        return;
    }
    
    showQuoteModal(selection.toString());
}

// Показать модалку для цитаты
function showQuoteModal(text) {
    const modal = document.createElement('div');
    modal.className = 'modal quote-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Добавить цитату</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="quote-preview">
                    <blockquote>${escapeHtml(text)}</blockquote>
                </div>
                <div class="form-group">
                    <label for="quoteNote">Заметка (необязательно)</label>
                    <textarea id="quoteNote" placeholder="Добавьте комментарий..." rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label for="quoteTags">Теги</label>
                    <input type="text" id="quoteTags" placeholder="философия, вдохновение, жизнь">
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="this.closest('.modal').remove()">Отмена</button>
                <button class="btn btn-primary" onclick="saveQuote('${encodeURIComponent(text)}')">Сохранить</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Закрытие модалки
    modal.querySelector('.modal-close').addEventListener('click', () => {
        modal.remove();
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Сохранение цитаты
async function saveQuote(text) {
    if (!currentUser) return;
    
    const decodedText = decodeURIComponent(text);
    const note = document.getElementById('quoteNote').value;
    const tags = document.getElementById('quoteTags').value.split(',').map(t => t.trim()).filter(t => t);
    
    try {
        const token = localStorage.getItem('token');
        const bookId = getCurrentBookId();
        const chapter = getCurrentChapter();
        
        const response = await fetch(`${API_BASE_URL}/quotes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bookId,
                chapter,
                text: decodedText,
                note,
                tags
            })
        });
        
        if (response.ok) {
            showNotification('Цитата сохранена', 'success');
            document.querySelector('.quote-modal').remove();
        }
    } catch (error) {
        console.error('Failed to save quote:', error);
        showNotification('Ошибка сохранения цитаты', 'error');
    }
}

// Настройка выделения текста
function setupQuoteSelection() {
    document.addEventListener('mouseup', (e) => {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        if (selectedText.length > 0 && e.target.closest('.reader-content')) {
            showSelectionToolbar(e.pageX, e.pageY, selectedText);
        }
    });
}

// Показать панель инструментов для выделенного текста
function showSelectionToolbar(x, y, text) {
    // Удаляем существующую панель
    const existingToolbar = document.querySelector('.selection-toolbar');
    if (existingToolbar) {
        existingToolbar.remove();
    }
    
    const toolbar = document.createElement('div');
    toolbar.className = 'selection-toolbar';
    toolbar.style.left = `${x}px`;
    toolbar.style.top = `${y - 40}px`;
    
    toolbar.innerHTML = `
        <button class="toolbar-btn" onclick="handleTextHighlight()" title="Добавить цитату">
            <i class="fas fa-quote-right"></i>
        </button>
        <button class="toolbar-btn" onclick="copyToClipboard('${encodeURIComponent(text)}')" title="Копировать">
            <i class="fas fa-copy"></i>
        </button>
        <button class="toolbar-btn" onclick="shareQuote('${encodeURIComponent(text)}')" title="Поделиться">
            <i class="fas fa-share"></i>
        </button>
    `;
    
    document.body.appendChild(toolbar);
    
    // Скрыть панель при клике вне ее
    setTimeout(() => {
        document.addEventListener('click', function hideToolbar(e) {
            if (!toolbar.contains(e.target)) {
                toolbar.remove();
                document.removeEventListener('click', hideToolbar);
            }
        });
    }, 100);
}

// Копирование в буфер обмена
async function copyToClipboard(text) {
    try {
        const decodedText = decodeURIComponent(text);
        await navigator.clipboard.writeText(decodedText);
        showNotification('Текст скопирован', 'success');
    } catch (error) {
        console.error('Copy failed:', error);
        showNotification('Ошибка копирования', 'error');
    }
}

// Поделиться цитатой
async function shareQuote(text) {
    const decodedText = decodeURIComponent(text);
    
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'Цитата из книги',
                text: decodedText,
                url: window.location.href
            });
        } catch (error) {
            console.error('Share failed:', error);
        }
    } else {
        copyToClipboard(text);
        showNotification('Цитата скопирована для публикации', 'info');
    }
}

// ==================== СОЦИАЛЬНЫЕ ФУНКЦИИ ====================

// Загрузка друзей и активности
async function loadSocialFeed() {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/social/feed`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
 {
            const feed = await response.json();
            renderSocialFeed(feed);
        }
    } catch (error) {
        console.error('Failed to load social feed:', error);
    }
}

// Отображение социальной ленты
function renderSocialFeed(feed) {
    const container = document.querySelector('.social-feed');
    if (!container) return;
    
    if (feed.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>Нет активности</h3>
                <p>Добавьте друзей или поделитесь своими достижениями</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = feed.map(item => `
        <div class="feed-item">
            <div class="feed-user">
                <img src="${item.user.avatar || '/default-avatar.png'}" alt="${item.user.username}">
                <div class="feed-user-info">
                    <strong>${item.user.username}</strong>
                    <span class="feed-time">${formatRelativeTime(item.createdAt)}</span>
                </div>
            </div>
            <div class="feed-content">
                ${getFeedContent(item)}
            </div>
            <div class="feed-actions">
                <button class="feed-action-btn" onclick="likelikeActivity('${item.id}')">
                    <i class="far fa-heart"></i> ${item.likes || 0}
                </button>
                <button class="feed-action-btn" onclick="commentOnActivity('${item.id}')">
                    <i class="far fa-comment"></i> ${item.comments || 0}
                </button>
                <button class="feed-action-btn" onclick="shareActivity('${item.id}')">
                    <i class="fas fa-share"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Получение контента для ленты
function getFeedContent(item) {
    switch(item.type) {
        case 'book_finished':
            return `
                <p>Завершил чтение книги</p>
                <div class="feed-book">
                    <img src="${item.book.cover}" alt="${item.book.title}">
                    <div>
                        <strong>${item.book.title}</strong>
                        <p>${item.book.author}</p>
                    </div>
                </div>
            `;
        case 'quote_shared':
            return `
                <p>Поделился цитатой из книги</p>
                <blockquote>${item.quote.text}</blockquote>
                <div class="feed-book">
                    <img src="${item.book.cover}" alt="${item.book.title}">
                    <div>
                        <strong>${item.book.title}</strong>
                    </div>
                </div>
            `;
        case 'review_added':
            return `
                <p>Оставил рецензию на книгу</p>
                <div class="feed-review">
                    <div class="review-rating">
                        ${'★'.repeat(item.review.rating)}${'☆'.repeat(5 - item.review.rating)}
                    </div>
                    <p>${item.review.text}</p>
                </div>
                <div class="feed-book">
                    <img src="${item.book.cover}" alt="${item.book.title}">
                    <div>
                        <strong>${item.book.title}</strong>
                    </div>
                </div>
            ` `;
        default:
            return `<p>${item.text}</p>`;
    }
}

// Форматирование относительного времени
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'только что';
    if (diffMins < 60) return `${diffMins} мин назад`;
    if (diffHours < 24) return `${diffHours} ч назад`;
    if (diffDays < 7) return `${diffDays} дн назад`;
    return date.toLocaleDateString('ru-RU');
}

// Лайк активности
async function likeActivity(activityId) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/social/like/${activityId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            loadSocialFeed();
();
        }
    } catch (error) {
        console.error('Failed to like activity:', error);
    }
}

// ==================== ОФФЛАЙН РЕЖИМ ====================

// Проверка онлайн-статуса
function setupOfflineSupport() {
    // Кэширование книг для оффлайн-чтения
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('ServiceWorker registered');
            })
            .catch(error => {
                console.log('ServiceWorker registration failed:', error);
            });
    }
    
    // Отслеживание онлайн-статуса
    window.addEventListener('online', () => {
        showNotification('Соединение восстановлено', 'success');
        syncOfflineData();
    });
    
    window.addEventListener('offline', () => {
        showNotification('Работаем в оффлайн-режиме', 'info');
    });
}

// Синхронизация оффлайн данных
async function syncOfflineData() {
    const offlineActions = JSON.parse(localStorage.getItem('offlineActions') || '[]');
    
    if (offlineActions.length === 0) return;
    
    for (const action of offlineActions) {
        try {
            await executeOfflineAction(action);
        } catch (error) {
            console.error('Failed to sync action:', action, error);
        }
    }
    
    localStorage.removeItem('offlineActions');
    showNotification('Данные синхронизированы', 'success');
}

// Выполнение оффлайн действия
async function executeOfflineAction(action) {
    const token = localStorage.getItem('token');
    
    const response = await fetch(`${API_BASE_URL}${action.endpoint}`, {
        method: action.method,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(action.data)
    });
    
    if (!response.ok) {
        throw new Error('Sync failed');
    }
}

// Сохранение действия для оффлайн-синхронизации
function saveOfflineAction(endpoint, method, data) {
    const actions = JSON.parse(localStorage.getItem('offlineActions') || '[]');
    actions.push({
        endpoint,
        method,
        data,
        timestamp: new Date().toISOString()
    });
    localStorage.setItem('offlineActions', JSON.stringify(actions));
}

// ==================== ПРОИЗВОДИТЕЛЬНОСТЬ ====================

// Ленивая загрузка изображений
function setupLazyLoading() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.dataset.src;
                if (src) {
                    img.src = src;
                    img.removeAttribute('data-src');
                }
                observer.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        observer.observe(img);
    });
}

// Кэширование запросов
const requestCache = new Map();

async function cachedFetch(url, options = {}) {
    const cacheKey = `${url}_${JSON.stringify(options)}`;
    
    // Проверяем кэш
    if (requestCache.has(cacheKey)) {
        const cached = requestCache.get(cacheKey);
        if (Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 минут
            return cached.data;
        }
    }
    
    // Выполняем запрос
    const response = await fetch(url, options);
    const data = await response.json();
    
    // Сохраняем в кэш
    requestCache.set(cacheKey, {
        data,
        timestamp: Date.now()
    });
    
    return data;
}

// Оптимизация скролла
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ==================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ====================

// Экспорт данных пользователя
async function exportUserData() {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/user/export`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            downloadJSON(data, `library-export-${new Date().toISOString().split('T')[0]}.json`);
            showNotification('Данные экспортированы', 'success');
        }
    } catch (error) {
        console.error('Export failed:', error);
        showNotification('Ошибка экспорта', 'error');
    }
}

// Скачивание JSON файла
function downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Импорт данных
function importUserData() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            
            if (confirm('Импортировать данные? Существующие данные могут быть перезаписаны.')) {
                await processImport(data);
            }
        } catch (error) {
            console.error('Import failed:', error);
            showNotification('Ошибка импорта файла', 'error');
        }
    };
    
    input.click();
}

// Обработка импорта
async function processImport(data) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/user/import`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Данные импортированы', 'success');
            location.reload();
        }
    } catch (error) {
        console.error('Import processing failed:', error);
        showNotification('Ошибка обработки импорта', 'error');
    }
}

// Темная тема
function setupThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    if (!themeToggle) return;
    
    // Проверяем сохраненную тему
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    themeToggle.addEventListener('click', () () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Обновляем иконку
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = newTheme === 'dark' ? 'fas fa-sun'' : 'fas fa-moon';
        }
    });
}

// ==================== ИНИЦИАЛИЗАЦИЯ ДОПОЛНИТЕЛЬНЫХ МОДУЛЕЙ ====================

// Обновленная функция инициализации
async function initApp() {
    // Проверка авторизации
    await checkAuth();
    
    // Инициализация компонентов
    initAuthModal();
    initNavigation();
    initSearch();
    initFilters();
    initBookGrid();
    initLists();
    initChatBot();
    initNotifications();
    initReader();
    initQuotesSystem();
    setupOfflineSupport();
    setupLazyLoading();
    setupSmoothScrolling();
    setupThemeToggle();
    
    // Загрузка данных
    loadBooks();
    loadUserLists();
    loadStats();
    loadRecommendations();
    loadSocialFeed();
    
    // Обработчики событий
    setupEventListeners();
    
    // Восстановление позиции чтения
    if (window.location.pathname.includes('/reader')) {
        restoreReadingPosition();
    }
}

// Экспорт дополнительных функций
window.exportUserData = exportUserData;
window.importUserData = importUserData;
window.copyToClipboard = copyToClipboard;
window.shareQuote = shareQuote;
window.likeActivity = likeActivity;

// Запуск приложения
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
