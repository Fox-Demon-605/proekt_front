// ==================== BACKEND API (Node.js + Express) ====================

const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

// Подключение к MongoDB
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/online-library', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// ==================== МОДЕЛИ ====================

// Модель пользователя
const userSchema = new mongoose.Schema({
    username: { type: String, required: true, unique: true },
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    avatar: { type: String, default: '' },
    bio: { type: String, default: '' },
    readingStats: {
        booksRead: { type: Number, default: 0 },
        pagesRead: { type: Number, default: 0 },
        readingTime: { type: Number, default: 0 },
        currentStreak: { type: Number, default: 0 },
        longestStreak: { type: Number, default: 0 }
    },
    preferences: {
        favoriteGenres: [{ type: String }],
        readingGoal: { type: Number, default: 12 },
        theme: { type: String, default: 'light' }
    },
    friends: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema);

// Модель книги
const bookSchema = new mongoose.Schema({
    title: { type: String, required: true },
    author: { type: String, required: true },
    description: { type: String, required: true },
    coverUrl: { type: String, default: '' },
    fileUrl: { type: String, required: true },
    genre: [{ type: String }],
    tags: [{ type: String }],
    pages: { type: Number, default: 0 },
    year: { type: Number },
    language: { type: String, default: 'ru' },
    rating: {
        average: { type: Number, default: 0 },
        count: { type: Number, default: 0 }
    },
    chapters: [{
        title: String,
        content: String,
        number: Number
    }],
    uploader: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    isPublic: { type: Boolean, default: true },
    createdAt: { type: Date, default: Date.now }
});

const Book = mongoose.model('Book', bookSchema);

// Модель списка чтения
const readingListSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    name: { type: String, required: true },
    books: [{
        bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book' },
        addedAt: { type: Date, default: Date.now },
        status: { type: String, enum: ['planned', 'reading', 'completed'], default: 'planned' }
    }],
    isPublic: { type: Boolean, default: false },
    createdAt: { type: Date, default: Date.now }
});

const ReadingList = mongoose.model('ReadingList', readingListSchema);

// Модель прогресса чтения
const readingProgressSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book', required: true },
    currentChapter: { type: Number, default: 0 },
    progress: { type: Number, default: 0 },
    lastReadAt: { type: Date, default: Date.now },
    timeSpent: { type: Number, default: 0 },
    completed: { type: Boolean, default: false },
    completedAt: { type: Date }
});

const ReadingProgress = mongoose.model('ReadingProgress', readingProgressSchema);

// Модель закладок
const bookmarkSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    bookIdId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book', required: true },
    chapter: { type: Number, required: true },
    position: { type: Number, default: 0 },
    note: { type: String, default: '' },
    createdAt: { type: Date, default: Date.now }
});

const Bookmark = mongoose.model('Bookmark', bookmarkSchema);

// Модель цитат
const quoteSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book', required: true },
    chapter: { type: Number, required: true },
    text text: { type: String, required: true },
    note: { type: String, default: '' },
    tags: [{ type: String }],
    isPublic: { type: Boolean, default: false },
    likes: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    createdAt: { type: Date, default: Date.now }
});

const Quote = mongoose.model('Quote', quoteSchema);

// Модель рецензий
const reviewSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book', required: true },
    rating: { type: Number, required: true, min: 1, max: 5 },
    text: { type: String, required: true },
 },
    likes: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
});

const Review = mongoose.model('Review', reviewSchema);

// Модель социальной активности
const activitySchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    type: { 
        type: String, 
        enum: ['book_finished', 'quote_shared', 'review_added', 'friend_added', 'goal_achieved'],
        required: true 
    },
    bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book' },
    quoteId: { type: mongoose.Schema.Types.ObjectId, ref: 'Quote' },
    reviewId: { type: mongoose.Schema.Types.ObjectId, ref: 'Review' },
    data: { type: mongoose.Schema.Types.Mixed },
    likes: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    comments: [{
        userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
        text: String,
        createdAt: { type: Date, default: Date.now }
    }],
    createdAt: { type: Date, default: Date.now }
});

const Activity = mongoose.model('Activity', activitySchema);

// ==================== MIDDLEWARE ====================

// Middleware для проверки JWT токена
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: 'Токен отсутствует' });
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ error: 'Неверный токен' });
        }
        req.user = user;
        next();
    });
};

// Middleware для загрузки файлов
const storage = multer.diskStorage({
    destination destination: (req, file, cb) => {
        const dir = 'uploads/';
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        cb(null, dir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    limits: { fileSize: 50 * 1024 * 1024 }, // 50MB
    fileFilter: (req, file, cb) => {
        const allowedTypes = /jpeg|jpg|png|gif|pdf|epub|txt/;
        const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = allowedTypes.test(file.mimetype);
        
        if (extname && mimetype) {
            return cb(null, true);
        } else {
            cb(new Error('Недопустимый тип файла'));
        }
    }
});

// ==================== РОУТЫ АВТОРИЗАЦИИ ====================

// Регистрация
app.post('/api/auth/register', async (req, res) => {
    try {
        const { username, email, password } = req.body;

        // Проверка существующего пользователя
        const existingUser = await User.findOne({ $or: [{ email }, { username }] });
        if (existingUser) {
            return res.status(400).json({ error: 'Пользователь уже существует' });
        }

        // Хэширование пароля
        const hashedPassword = await bcrypt.hash(password, 10);

        // Создание пользователя
        const user = new User({
            username,
            email,
            password: hashedPassword
        });

        await user.save();

        // Генерация токена
        const token = jwt.sign(
            { userId: user._id, username: user.username },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.status(201).json({
            token,
            user: {
                id: user._id,
                username: user.username,
                email: user.email,
                avatar: user.avatar
            }
        });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ error: 'Ошибка регистрации' });
    }
});

// Вход
app.post('/api/auth/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Поиск пользователя
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(401).json({ error: 'Неверные учетные данные' });
        }

        // Проверка пароля
        const validPassword = await bcrypt.compare(password, user.password);
        if (!validPassword) {
            return res.status(401).json({ error: 'Неверные учетные данные' });
        }

        // Генерация токена
        const token = jwt.sign(
            { userId: user._id, username: user.username },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.json({
            token,
            user: {
                id: user._id,
                username: user.username,
                email: user.email,
                avatar: user.avatar,
                readingStats: user.readingStats,
                preferences: user.preferences
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Ошибка входа' });
    }
});

// Получение профиля
app.get('/api/auth/profile', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId)
            .select('-password')
            .populate('friends', 'username avatar');
        
        if (!user) {
            return res.status(404).json({ error: 'Пользователь не найден' });
        }

        res.json({ user });
    } catch (error) {
        console.error('Profile error:', error);
        res.status(500).json({ error: 'Ошибка получения профиля' });
    }
});

// Обновление профиля
app.put('/api/auth/profile', authenticateToken, upload.single('avatar'), async (req, res) => {
    try {
        const updates = req.body;
        const user = await User.findById(req.user.userId);
        
        if (!user) {
            return res.status(404).json({ error: 'Пользователь не найден' });
        }

        // Обновление аватара
        if (req.file) {
            updates.avatar = `/uploads/${req.file.filename}`;
        }

        // Обновление пароля
        if (updates.password) {
            updates.password = await bcrypt.hash(updates.password, 10);
        }

        Object.assign(user, updates);
        await user.save();

        res.json({
            user: {
                id: user._id,
                username: user.username,
                email: user.email,
                avatar: user.avatar,
                bio: user.bio,
                readingStats: user.readingStats,
                preferences: user.preferences
            }
        });
    } catch (error) {
        console.error('Update profile error:', error);
        res.status(500).json({ error: 'Ошибка обновления профиля' });
    }
});

// ==================== РОУТЫ КНИГ ====================

// Получение всех книг
app.get('/api/books', async (req, res) => {
    try {
        const { 
            page = 1, 
            limit = 20, 
            genre, 
            author, 
            search,
            sort = 'createdAt',
            order = 'desc'
        } = req.query;

        const query = { isPublic: true };
        
        // Фильтрация
        if (genre) query.genre = genre;
        if (author) query.author = new RegExp(author, 'i');
        if (search) {
            query.$or = [
                { title: new RegExp(search, 'i') },
                { author: new RegExp(search, 'i') },
                { description: new RegExp(search, 'i') }
            ];
        }

        // Сортировка
        const sortOptions = {};
        sortOptions[sort] = order === 'desc' ? -1 : 1;

        // Пагинация
        const skip = (page - 1) * limit;

        const books = await Book.find(query)
            .sort(sortOptions)
            .skip(skip)
            .limit(parseInt(limit))
            .populate('uploader', 'username avatar');

        const total = await Book.countDocuments(query);

        res.json({
            books,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit),
                total,
                pages: Math.ceil(total / limit)
            }
        });
    } catch (error) {
        console.error('Get books error:', error);
        res.status(500).json({ error: 'Ошибка получения книг' });
    }
});

// Получение книги по ID
app.get('/api/books/:id', async (req, res) => {
    try {
        const book = await Book.findById(req.params.id)
            .populate('uploader', 'username avatar');
        
        if (!book) {
            return res.status(404).json({ error: 'Книга не найдена' });
        }

        // Получение рейтинга и рецензий
        const reviews = await Review.find({ bookId: book._id })
            .populate('userId', 'username avatar')
            .sort({ createdAt: -1 })
            .limit(10);

        const averageRating = await Review.aggregate([
            { $match: { bookId: book._id } },
            { $group: { _id: null, average: { $avg: '$rating' } } }
        ]);

        book.rating = {
            average: averageRating[0]?.average || 0,
            count: reviews.length
        };

        res.json({ book, reviews });
    } catch (error) {
        console.error('Get book error:', error);
        res.status(500).json({ error: 'Ошибка получения книги' });
    }
});

// Загрузка новой книги
app.post('/api/books', authenticateToken, upload.fields([
    { name: 'cover', maxCount: 1 },
    { name: 'file', maxCount: 1 }
]), async (req, res) => {
    try {
        const { title, author, description, genre, tags, year, language } = req.body;
        
        if (!req.files.file) {
            return res res.status(400).json({ error: 'Файл книги обязателен' });
        }

        const book = new Book({
            title,
            author,
            description,
            genre: genre ? genre.split(',') : [],
            tags: tags ? tags.split(',') : [],
            year,
            language,
            coverUrl: req.files.cover ? `/uploads/${req.files.cover[0].filename}` : '',
            fileUrl: `/uploads/${req.files.file[0].filename}`,
            uploader: req.user.userId
        });

        await book.save();

        // Создание активности
        const activity = new Activity({
            userId: req.user.userId,
            type: 'book_uploaded',
            bookId: book._id,
            data: { title: book.title }
        });
        await activity.save();

        res.status(201).json({ book });
    } catch (error) {
        console.error('Upload book error:', error);
        res.status(500).json({ error: 'Ошибка загрузки книги' });
    }
});

// Обновление книги
app.put('/api/books/:id', authenticateToken, async (req, res) => {
    try {
        const book = await Book.findById(req.params.id);
        
        if (!book) {
            return res.status(404).json({ error: 'Книга не найдена' });
        }

        // Проверка прав
        if (book.uploader.toString() !== req.user.userId) {
            return res.status(403).json({ error: 'Нет прав на редактирование' });
        }

        Object.assign(book, req.body);
        await book.save();

        res.json({ book });
    } catch (error) {
        console.error('Update book error:', error);
        res.status(500).json({ error: 'Ошибка обновления книги' });
    }
});

// Удаление книги
app.delete('/api/books/:id', authenticateToken, async (req, res) => {
    try {
        const book = await Book.findById(req.params.id);
        
        if (!book) {
            return res.status(404).json({ error: 'Книга не найдена' });
        }

        // Проверка прав
        if (book.uploader.toString() !== req.user.userId) {
            return res.status(403).json({ error: 'Нет прав на удаление' });
        }

        // Удаление файлов
        if (book.coverUrl) {
            fs.unlinkSync(path.join(__dirname, book.coverUrl));
        }
        if (book.fileUrl) {
            fs.unlinkSync(path.join(__dirname, book.fileUrl));
        }

        await book.deleteOne();

        // Удаление связанных данных
        await ReadingProgress.deleteMany({ bookId: book._id });
        await Bookmark.deleteMany({ bookId: book._id });
        await Quote.deleteMany({ bookId: book._id });
        await Review.deleteMany({ bookId: book._id });

        res.json({ message: 'Книга удалена' });
    } catch (error) {
        console.error('Delete book error:', error);
        res.status(500).json({ error: 'Ошибка удаления книги' });
    }
});

// ==================== РОУТЫ ЧТЕНИЯ ====================

// Получение главы книги
app.get('/api/reading/chapter/:bookId/:chapter', authenticateToken, async (req, res) => {
    try {
        const { bookId, chapter } = req.params;
        const chapterNum = parseInt(chapter);

        const book = await Book.findById(bookId);
        if (!book) {
            return res.status(404).json({ error: 'Книга не найдена' });
        }

        if (chapterNum < 0 || chapterNum >= book.chapters.length) {
            return res.status(404).json({ error: 'Глава не найдена' });
        }

        const chapterData = book.chapters[chapterNum];
        
        // Обновление прогресса
        await ReadingProgress.findOneAndUpdate(
            { userId: req.user.userId, bookId },
            { 
                currentChapter: chapterNum,
                lastReadAt: new Date(),
                $inc: { timeSpent: 5 } // Пример: 5 минут на чтение
            },
            { upsert: true, new: true }
        );

        res.json({
            title: chapterData.title,
            number: chapterNum,
            content: chapterData.content,
            totalChapters: book.chapters.length
        });
    } catch (error) {
        console.error('Get chapter error:', error);
        res.status(500).json({ error: 'Ошибка получения главы' });
    }
});

// Обновление прогресса чтения
app.post.post('/api/reading/progress', authenticateToken, async (req, res) => {
    try {
        const { bookId, chapter, progress } = req.body;

        const progressDoc = await ReadingProgress.findOneAndUpdate(
            { userId: req.user.userId, bookId },
            {
                currentChapter: chapter,
                progress,
                lastReadAt: new Date(),
                $inc: { timeSpent: 1 }
            },
            { upsert: true, new: true }
        );

        // Проверка завершения книги
        const book = await Book.findById(bookId);
        if (progress >= 100 && !progressDoc.completed) {
            progressDoc.completed = true;
            progressDoc.completedAt = new Date();
            await progressDoc.save();

            // Обновление статистики пользователя
            await User.findByIdAndUpdate(req.user.userId, {
                $inc: { 
                    'readingStats.booksRead': 1,
                    'readingStats.pagesRead': book.pages || 0
                }
            });

            // Создание активности
            const activity = new Activity({
                userId: req.user.userId,
                type: 'book_finished',
                bookId,
                data: { title: book.title }
            });
            await activity.save();
        }

        res.json({ progress: progressDoc });
    } catch (error) {
        console.error('Update progress error:', error);
        res.status(500).json({ error: 'Ошибка обновления прогресса' });
    }
});

// Получение текущего прогресса
app.get('/api/reading/progress/:bookId', authenticateToken, async (req, res) => {
    try {
        const progress = await ReadingProgress.findOne({
            userId: req.user.userId,
            bookId: req.params.bookId
        });

        res.json({ progress: progress || null });
    } catch (error) {
        console.error('Get progress error:', error);
        res.status(500).json({ error: 'Ошибка получения прогресса' });
    }
});

// ==================== РОУТЫ СПИСКОВ ЧТЕНИЯ ====================

// Получение списков пользователя
app.get('/api/lists', authenticateToken, async (req, res) => {
    try {
        const lists = await ReadingList.find({ userId: req.user.userId })
            .populate('books.bookId', 'title author coverUrl')
            .sort({ createdAt: -1 });

        res.json({ lists });
    } catch (error) {
        console.error('Get lists error:', error);
        res.status(500).json({ error: 'Ошибка получения списков' });
    }
});

// Создание списка
app.post('/api/lists', authenticateToken, async (req, res) => {
    try {
        const { name, isPublic } = req.body;

        const list = new ReadingList({
            userId: req.user.userId,
            name,
            isPublic: isPublic || false
        });

        await list.save();

        res.status(201).json({ list });
    } catch (error) {
        console.error('Create list error:', error);
        res.status(500).json({ error: 'Ошибка создания списка' });
    }
});

// Добавление книги в список
app.post('/api/lists/:listId/books', authenticateToken, async (req, res) => {
    try {
        const { bookId, status } = req.body;

        const list = await ReadingList.findOne({
            _id: req.params.listId,
            userId: req.user.userId
        });

        if (!list) {
            return res.status(404).json({ error: 'Список не найден' });
        }

        // Проверка существования книги в списке
        const existingBook = list.books.find(b => b.bookId.toString() === bookId);
        if (existingBook) {
            return res.status(400).json({ error: 'Книга уже в списке' });
        }

        list.books.push({
            bookId,
            status: status || 'planned'
        });

        await list.save();

        res.json({ list });
    } catch (error) {
        console.error('Add to list error:', error);
        res.status(500).json({ error: 'Ошибка добавления в список' });
    }
});

// Обновление статуса книги в списке
app.put('/api/lists/:listId/books/:bookId', authenticateToken, async (req, res) => {
    try {
        const { status } = req.body;

        const list = await ReadingList.findOne({
            _id: req.params.listId,
            userId: req.user.userId
        });

        if (!list) {
            return res.status(404).json({ error: 'Список не найден' });
        }

        const bookIndex = list.books.findIndex(b => b.bookId.toString() === req.params.bookId);
        if (bookIndex === -1) {
            return res.status(404).json({ error: 'Книга не найдена в списке' });
        }

        list.books[bookIndex].status = status;
        await list.save();

        res.json({ list });
    } catch (error) {
        console.error('Update list book error:', error);
        res.status(500).json({ error: 'Ошибка обновления списка' });
    }
});

// Удаление книги из списка
app.delete('/api/lists/:listId/books/:bookId', authenticateToken, async (req, res) => {
    try {
        const list = await ReadingList.findOne({
            _id: req.params.listId,
            userId: req.user.userId
        });

        if (!list) {
            return res.status(404).json({ error: 'Список не найден' });
        }

        list.books = list.books.filter(b => b.bookId.toString() !== req.params.bookId);
        await list.save();

        res.json({ list });
    } catch (error) {
        console.error('Remove from list error:', error);
        res.status(500).json({ error: 'Ошибка удаления из списка' });
    }
});

// ==================== РОУТЫ ЗАКЛАДОК ====================

// Получение закладок пользователя
app.get('/api/bookmarks', authenticateToken, async (req, res) => {
    try {
        const bookmarks = await Bookmark.find({ userId: req.user.userId })
            .populate('bookId', 'title author coverUrl')
            .sort({ createdAt: -1 });

        res.json({ bookmarks });
    } catch (error) {
        console.error('Get bookmarks error:', error);
        res.status(500).json({ error: 'Ошибка получения закладок' });
    }
});

// Добавление/удаление закладки
app.post('/api/bookmarks', authenticateToken, async (req, res) => {
    try {
        const { bookId, chapter, position, note } = req.body;

        // Проверка существующей закладки
        const existingBookmark = await Bookmark.findOne({
            userId: req.user.userId,
            bookId,
            chapter
        });

        if (existingBookmark) {
            await existingBookmark.deleteOne();
            return res.json({ bookmarked: false });
        }

        const bookmark = new Bookmark({
            userId: req.user.userId,
            bookId,
            chapter,
            position,
            note
        });

               await bookmark.save();

        res.json({ bookmarked: true, bookmark });
    } catch (error) {
        console.error('Toggle bookmark error:', error);
        res.status(500).json({ error: 'Ошибка работы с закладкой' });
    }
});

// ==================== РОУТЫ ЦИТАТ ====================

// Получение цитат пользователя
app.get('/api/quotes', authenticateToken, async (req, res) => {
    try {
        const quotes = await Quote.find({ userId: req.user.userId })
            .populate('bookId', 'title author coverUrl')
            .sort({ createdAt: -1 });

        res.json({ quotes });
    } catch (error) {
        console.error('Get quotes error:', error);
        res.status(500).json({ error: 'Ошибка получения цитат' });
    }
});

// Добавление цитаты
app.post('/api/quotes', authenticateToken, async (req, res) => {
    try {
        const { bookId, chapter, text, note, tags } = req.body;

        const quote = new Quote({
            userId: req.user.userId,
            bookId,
            chapter,
            text,
            note,
            tags: tags || []
        });

        await quote.save();

        // Создание активности
        const activity = new Activity({
            userId: req.user.userIdId,
            type: 'quote_shared',
            bookId,
            quoteId: quote._id,
            data: { text: quote.text.substring(0, 100) + '...' }
        });
        await activity.save();

        res.status(201).json({ quote });
    } catch (error) {
        console.error('Add quote error:', error);
        res.status(500).json({ error: 'Ошибка добавления цитаты' });
    }
});

// ==================== РОУТЫ РЕЦЕНЗИЙ ====================

// Добавление рецензии
app.post('/api/reviews', authenticateToken, async (req, res) => {
    try {
        const { bookId, rating, text } = req.body;

        // Проверка существующей рецензии
        const existingReview = await Review.findOne({
            userId: req.user.userId,
            bookId
        });

        if (existingReview) {
            return res.status(400).json({ error: 'Рецензия уже существует' });
        }

        const review = new Review({
            userId: req.user.userId,
            bookId,
            rating,
            text
        });

        await review.save();

        // Обновление рейтинга книги
        await updateBookRating(bookId);

        // Создание активности
        const activity = new Activity({
            userId: req.user.userId,
            type: 'review_added',
            bookId,
            reviewId: review._id,
            data: { rating, text: text.substring(0, 100) + '...' }
        });
        await activity.save();

        res.status(201).json({ review });
    } catch (error) {
        console.error('Add review error:', error);
        res.status(500).json({ error: 'Ошибка добавления рецензии' });
    }
});

// Обновление рейтинга книги
async function updateBookRating(bookId) {
    const result = await Review.aggregate([
        { $match: { bookId: mongoose.Types.ObjectId(bookId) } },
        { 
            $group: {
                _id: null,
                average: { $avg: '$rating' },
                count: { $sum: 1 }
            }
        }
    ]);

    if (result.length > 0) {
        await Book.findByIdAndUpdate(bookId, {
            'rating.average': result[0].average,
            'rating.count': result[0].count
        });
    }
}

// ==================== РОУТЫ РЕКОМЕНДАЦИЙ ====================

// Получение рекомендаций
app.get('/api/recommendations', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId);
        
        // Получение прочитанных книг
        const progress = await ReadingProgress.find({ 
            userId: req.user.userId,
            completed: true 
        }).populate('bookId');

        const readBookIds = progress.map(p => p.bookId._id);
        const favoriteGenres = user.preferences.favoriteGenres || [];

        // Поиск рекомендаций
        let query = { 
            _id: { $nin: readBookIds },
            isPublic: true 
        };

        if (favoriteGenres.length > 0) {
            query.genre = { $in: favoriteGenres };
        }

        const recommendations = await Book.find(query)
            .sort({ 'rating.average': -1, 'rating.count': -1 })
            .limit(10)
            .populate('uploader', 'username avatar');

        // Добавление причины рекомендации
        const recommendationsWithReason = recommendations.map(book => ({
            ...book.toObject(),
            reason: favoriteGenres.length > 0 ? 
                'На основе ваших любимых жанров' : 
                'Популярные книги на платформе'
        }));

        res.json(recommendationsWithReason);
    } catch (error) {
        console.error('Get recommendations error:', error);
        res.status(500).json({ error: 'Ошибка получения рекомендаций' });
    }
});

// ==================== РОУТЫ СОЦИАЛЬНЫХ ФУНКЦИЙ ====================

// Получение социальной ленты
app.get('/api/social/feed', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId);
        
        // Получение активности друзей и пользователя
        const feed = await Activity.find({
            $or: [
                { userId: { $in: user.f.friends } },
                { userId: req.user.userId }
            ]
        })
        .populate('userId', 'username avatar')
        .populate('bookId', 'title author coverUrl')
        .populate('quoteId', 'text')
        .populate('reviewId', 'rating text')
        .sort({ createdAt: -1 })
        .limit(20);

        res.json(feed);
    } catch (error) {
        console.error('Get feed error:', error);
        res.status(500).json({ error: 'Ошибка получения ленты' });
    }
});

// Лайк активности
app.post('/api/social/like/:activityId', authenticateToken, async (req, res) => {
    try {
        const activity = await Activity.findById(req.params.activityId);
        
        if (!activity) {
            return res.status(404).json({ error: 'Активность не найдена' });
        }

        const likeIndex = = activity.likes.indexOf(req.user.userId);
        
        if (likeIndex === -1) {
            activity.likes.push(req.user.userId);
        } else {
            activity.likes.splice(likeIndex, 1);
        }

        await activity.save();

        res.json({ likes: activity.likes.length });
    } catch (error) {
        console.error('Like activity error:', error);
        res.status(500).json({ error: 'Ошибка лайка' });
    }
});

// Поиск пользователей
app.get('/api/social/users', authenticateToken, async (req, res) => {
    try {
        const { search } = req.query;
        
        const query = { 
            _id: { $ne: req.user.userId } // Исключаем текущего пользователя
        };

        if (search) {
            query.$or = [
                { username: new RegExp(search, 'i') },
              { email: new RegExp(search, 'i') }
            ];
        }

        const users = await User.find(query)
            .select('username avatar bio readingStats')
            .limit(20);

        res.json({ users });
    } catch (error) {
        console.error('Search users error:', error);
        res.status(500).json({ error: 'Ошибка поиска пользователей' });
    }
});

// Добавление в друзья
app.post('/api/social/friends/:userId', authenticateToken, async (req, res) => {
    try {
        const friendId = req.params.userId;
        
        if (friendId === req.user.userId) {
            return res.status(400).json({ error: 'Нельзя добавить себя в друзья' });
        }

        const user = await User.findById(req.user.userId);
        const friend = await User.findById(friendId);

        if (!friend) {
            return res.status(404).json({ error: 'Пользователь не найден' });
        }

        // Проверка, уже ли в друзьях
        if (user.friends.includes(friendId)) {
            return res.status(400).json({ error: 'Пользователь уже в друзьях' });
        }

        user.friends.push(friendId);
        await user.save();

        // Создание активности
        const activity = new Activity({
            userId: req.user.userId,
            type: 'friend_added',
            data: { friendUsername: friend.username }
        });
        await activity.save();

        res.json({ 
            message: 'Пользователь добавлен в друзья',
            friend: {
                id: friend._id,
                username: friend.username,
                avatar: friend.avatar
            }
        });
    } catch (error) {
        console.error('Add friend error:', error);
        res.status(500).json({ error: 'Ошибка добавления в друзья' });
    }
});

// Удаление из друзей
app.delete('/api/social/friends/:userId', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId);
        
        user.friends = user.friends.filter(friendId => 
            friendId.toString() !== req.params.userId
        );
        
        await user.save();
        
        res.json({ message: 'Пользователь удален из друзей' });
    } catch (error) {
        console.error('Remove friend error:', error);
        res.status(500).json({ error: 'Ошибка удаления из друзей' });
    }
});

// ==================== РОУТЫ СТАТИСТИКИ ====================

// Получение статистики пользователя
app.get('/api/stats/user', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId)
            .select('readingStats preferences');
        
        // Получение прогресса по целям
        const currentMonth = new Date().getMonth();
        const currentYearYear = new Date().getFullYear();
        
        const monthlyProgress = await ReadingProgress.aggregate([
            {
                $match: {
                    userId: mongoose.Types.ObjectId(req.user.userId),
                    completed: true,
                    completedAt: {
                        $gte: new Date(currentYear, currentMonth, 1),
                        $lt: new Date(currentYear, currentMonth + 1, 1)
                    }
                }
            },
            { $count: "booksRead" }
        ]);

        const readingGoalProgress = {
            current: monthlyProgress[0]?.booksRead || 0,
            goal: user.preferences.readingGoal || 12,
            percentage: Math.min(
                ((monthlyProgress[0]?.booksRead || 0) / (user.preferences.readingGoal || 12)) * 100,
                100
            )
        };

        // Получение любимых жанров
        const genreStats = await ReadingProgress.aggregate([
            {
                $match: {
                    userId: mongoose.Types.ObjectId(req.user.userId),
                    completed: true
                }
            },
            {
                $lookup: {
                    from: 'books',
                    localField: 'bookId',
                    foreignField: '_id',
                    as: 'book'
                }
            },
            { $unwind: '$book' },
            { $unwind: '$book.genre' },
            {
                $group: {
                    _id: '$book.genre',
                    count: { $sum: 1 }
                }
            },
 },
            { $sort: { count: -1 } },
            { $limit: 5 }
        ]);

        res.json({
            readingStats: user.readingStats,
            readingGoalProgress,
            favoriteGenres: genreStats,
            preferences: user.preferences
        });
    } catch (error) {
        console.error('Get user stats error:', error);
        res.status(500).json({ error: 'Ошибка получения статистики' });
    }
});

// Получение глобальной статистики
app.get('/api/stats/global', async (req, res) => {
    try {
        const [
            totalBooks,
            totalUsers,
            totalPagesRead,
            mostPopularBooks,
            mostActiveReaders
        ] = await Promise.all([
            Book.countDocuments({ isPublic: true }),
            User.countDocuments(),
            User.aggregate([
                { $group: { _id: null, total: { $sum: '$readingStats.pagesRead' } } }
            ]),
            Book.find({ isPublic: true })
                .sort({ 'rating.average': -1, 'rating.count': -1 })
                .limit(5)
                .select('title author coverUrl rating'),
            User.find()
                .sort({ 'readingStats.booksRead': -1 })
                .limit(5)
                .select('username avatar readingStats')
        ]);

        res.json({
            totalBooks,
            totalUsers,
            totalPagesRead: totalPagesRead[0]?.total || 0,
            mostPopularBooks,
            mostActiveReaders
        });
    } catch (error) {
        console.error('Get global stats error:', error);
        res.status(500).json({ error: 'Ошибка получения глобальной статистики' });
    }
});

// ==================== РОУТЫ УВЕДОМЛЕНИЙ ====================

// Получение уведомлений пользователя
app.get('/api/notifications', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId);
        
        // Получение уведомлений о лайках, комментариях и друзьях
        const notifications = await Activity.find({
            $or: [
                { likes: req.user.userId },
                { 'comments.userId': req.user.userId },
                { 
                    type: 'friend_added',
                    'data.friendUsername': user.username 
                }
            ]
        })
        .populate('userId', 'username avatar')
        .sort({ createdAt: -1 })
        .limit(50);

        // Форматирование уведомлений
        const formattedNotifications = notifications.map(activity => {
            let message = '';
            let type = '';

            switch (activity.type) {
                case 'book_finished':
                    message = `${activity.userId.username} завершил(а) книгу "${activity.data?.title}"`;
                    type = 'book';
                    break;
                case 'quote_shared':
                    message = `${activity.userId.username} поделился(ась) цитатой`;
                    type = 'quote';
                    break;
                case 'review_added':
                    message = `${activity.userId.username} оставил(а) рецензию`;
                    type = 'review';
                    break;
                case 'friend_added':
                    message = `${activity.userId.username} добавил(а) вас в друзья`;
                    type = 'friend';
                    break;
                default:
                    message = 'Новое уведомление';
                    type = 'general';
            }

            return {
                id: activity._id,
                message,
                type,
                data: activity.data,
                userId: activity.userId,
                createdAt: activity.createdAt,
                read: false // В реальном приложении нужно хранить статус прочтения
            };
        });

        res.json({ notifications: formattedNotifications });
    } catch (error) {
        console.error('Get notifications error:', error);
        res.status(500).json({ error: 'Ошибка получения уведомлений' });
    }
});

// ==================== РОУТЫ АДМИНИСТРИРОВАНИЯ ====================

// Получение всех пользователей (только для админов)
app.get('/api/admin/users', authenticateToken, async (req, res) => {
    try {
        // Проверка прав администратора (в реальном приложении нужна система ролей)
        const user = await User.findById(req.user.userId);
        // Здесь должна быть проверка роли пользователя
        
        const users = await User.find()
            .select('username email avatar readingStats createdAt')
            .sort({ createdAt: -1 });

        res.json({ users });
    } catch (error) {
        console.error('Get all users error:', error);
        res.status(500).json({ error: 'Ошибка получения пользователей' });
    }
});

// Получение всех книг для модерации
app.get('/api/admin/books', authenticateToken, async (req, res) => {
    try {
        const books = await Book.find()
            .populate('uploader', 'username email')
            .sort({ createdAt: -1 });

        res.json({ books });
    } catch (error) {
        console.error('Get all books error:', error);
        res.status(500).json({ error: 'Ошибка получения книг' });
    }
});

// Изменение статуса книги (публичная/скрытая)
app.put('/api/admin/books/:id/status', authenticateToken, async (req, res) => {
    try {
        const { isPublic } = req.body;
        
        const book = await Book.findByIdAndUpdate(
            req.params.id,
            { isPublic },
            { new: true }
        );

        if (!book) {
            return res.status(404).json({ error: 'Книга не найдена' });
        }

        res.json({ book });
    } catch (error) {
        console.error('Update book status error:', error);
        res.status(500).json({ error: 'Ошибка обновления статуса книги' });
    }
});

// ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

// Функция для обновления стрика чтения
async function updateReadingStreak(userId) {
    const user = await User.findById(userId);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Проверка чтения сегодня
    const todayProgress = await ReadingProgress.findOne({
        userId,
        lastReadAt: { $gte: today }
    });
    
    if (todayProgress) {
        // Проверка чтения вчера
        const yesterdayProgress = await ReadingProgress.findOne({
            userId,
            lastReadAt: { 
                $gte: yesterday,
                $lt: today
            }
        });
        
        if (yesterdayProgress) {
            // Продолжение стрика
            user.readingStats.currentStreak += 1;
        } else {
            // Начало нового стрика
            user.readingStats.currentStreak = 1;
        }
        
        // Обновление самого длинного стрика
        if (user.readingStats.currentStreak > user.readingStats.longestStreak) {
            user.readingStats.longestStreak = user.readingStats.currentStreak;
        }
        
        await user.save();
    }
}

// Функция для ежедневного обновления стриков
async function updateAllStreaks() {
    const users = await User.find();
    
    for (const user of users) {
        await updateReadingStreak(user._id);
    }
}

// Запуск ежедневного обновления стриков
setInterval(updateAllStreaks, 24 * 60 * 60 * 1000); // Каждые 24 часа

// ==================== ОБРАБОТКА ОШИБОК ====================

// Обработка 404
app.use((req, res) => {
    res.status(404).json({ error: 'Маршрут не найден' });
});

// Обработка ошибок
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    
    if (err instanceof multer.MulterError) {
        if (err.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'Файл слишком большой' });
        }
    }
    
    res.status(500).json({ 
        error: 'Внутренняя ошибка сервера',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// ==================== ЗАПУСК СЕРВЕРА ====================

app.listen(PORT, () => {
    console.log(`Сервер запущен на порту ${PORT}`);
    console.log(`API доступен по адресу: http://localhost:${PORT}`);
});

// Экспорт для тестирования
module.exports = app;

// ==================== РОУТЫ ЭКСПОРТА/ИМПОРТА ====================

// Экспорт данных пользователя
app.get('/api/user/export', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId)
            .select('-password -refreshToken')
            .populate('friends', 'username email')
            .populate('readingLists.books', 'title author')
            .lean();

        const readingProgress = await ReadingProgress.find({ userId: req.user.userId })
            .populate('bookId', 'title author genre')
            .lean();

        const quotes = await Quote.find({ userId: req.user.userId })
            .populate('bookId', 'title author')
            .lean();

        const reviews = await Review.find({ userId: req.user.userId })
            .populate('bookId', 'title author')
            .lean();

        const exportData = {
            user,
            readingProgress,
            quotes,
            reviews,
            exportDate: new Date().toISOString(),
            version: '1.0'
        };

        // Формирование JSON файла
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Content-Disposition', 'attachment; filename="library_export.json"');
        res.json(exportData);
    } catch (error) {
        console.error('Export error:', error);
        res.status(500).json({ error: 'Ошибка экспорта данных' });
    }
});

// Импорт данных пользователя
app.post('/api/user/import', authenticateToken, upload.single('importFile'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'Файл не загружен' });
        }

        const importData = JSON.parse(req.file.buffer.toString());
        
        // Валидация структуры импортируемых данных
        if (!importData.user || !importData.version) {
            return res.status(400).json({ error: 'Неверный формат файла импорта' });
        }

        // Импорт цитат
        if (importData.quotes && Array.isArray(importData.quotes)) {
            for (const quote of importData.quotes) {
                const existingQuote = await Quote.findOne({
                    userId: req.user.userId,
                    'text': quote.text,
                    'bookId': quote.bookId
                });

                if (!existingQuote) {
                    await Quote.create({
                        ...quote,
                        userId: req.user.userId
                    });
                }
            }
        }

        // Импорт рецензий
        if (importData.reviews && Array.isArray(importData.reviews)) {
            for (const review of importData.reviews) {
                const existingReview = await Review.findOne({
                    userId: req.user.userId,
                    bookId: review.bookId
                });

                if (!existingReview) {
                    await Review.create({
                        ...review,
                        userId: req.user.userId
                    });
                }
            }
        }

        res.json({ message: 'Данные успешно импортированы' });
    } catch (error) {
        console.error('Import error:', error);
        res.status(500).json({ error: 'Ошибка импорта данных' });
    }
});

// ==================== РОУТЫ АУДИОКНИГ ====================

// Загрузка аудиофайла для книги
app.post('/api/books/:id/audio', authenticateToken, upload.single('audioFile'), async (req, res) => {
    try {
        const book = await Book.findById(req.params.id);
        
        if (!book) {
            return res.status(404).json({ error: 'Книга не найдена' });
        }

        // Проверка прав (только владелец или админ)
        if (book.uploader.toString() !== req.user.userId) {
            return res.status(403).json({ error: 'Нет прав для загрузки аудио' });
        }

        // Проверка формата файла
        const allowedFormats = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg'];
        if (!allowedFormats.includes(req.file.mimetype)) {
            return res.status(400).json({ error: 'Неподдерживаемый формат аудио' });
        }

        // Сохранение аудиофайла
        const audioUrl = await uploadToCloudStorage(req.file, 'audio-books');
        
        // Обновление книги
        book.audioUrl = audioUrl;
        book.hasAudio = true;
        await book.save();

        res.json({ 
            message: 'Аудиофайл успешно загружен',
            audioUrl 
        });
    } catch (error) {
        console.error('Upload audio error:', error);
        res.status(500).json({ error: 'Ошибка загрузки аудиофайла' });
    }
});

// Получение прогресса прослушивания аудиокниги
app.get('/api/audio/progress/:bookId', authenticateToken, async (req, res) => {
    try {
        const progress = await AudioProgress.findOne({
            userId: req.user.userId,
,
            bookId: req.params.bookId
        });

        res.json({ progress: progress || null });
    } catch (error) {
        console.error('Get audio progress error:', error);
        res.status(500).json({ error: 'Ошибка получения прогресса' });
    }
});

// Сохранение прогресса прослушивания
app.post('/api/audio/progress/:bookId', authenticateToken, async (req, res) => {
    try {
        const { currentTime, duration, chapter } = req.body;
        
        const progress = await AudioProgress.findOneAndUpdate(
            {
                userId: req.user.userId,
                bookId: req.params.bookId
            },
            {
                currentTime,
                duration,
                chapter,
                lastListenedAt: new Date()
            },
            { upsert: true, new: true }
        );

        res.json({ progress });
    } catch (error) {
        console.error('Save audio progress error:', error);
        res.status(500).json({ error: 'Ошибка сохранения прогресса' });
    }
});

// ==================================== РОУТЫ ОФФЛАЙН-РЕЖИМА ====================

// Получение книг для оффлайн-доступа
appapp.get('/api/offline/books', authenticateToken, async (req, res) => {
    try {
        const { limit = 20, page = 1 } = req.query;
        const skip = (page - 1) * limit;

        // Книги из списков чтения пользователя
        const user = await User.findById(req.user.userId)
            .populate({
                path: 'readingLists.books',
                match: { isPublic: true },
                select: 'title author coverUrl genre pages rating'
            });

        const allBooks = [];
        user.readingLists.forEach(list => {
            allBooks.push(...list.books);
        });

        // Уникальные книги
        const uniqueBooks = [...new Map(allBooks.map(book => [book._id.toString(), book])).values()];
        
        // Пагинация
        const paginatedBooks = uniqueBooks.slice(skip, skip + parseInt(limit));

        res.json({
            books: paginatedBooks,
            total: uniqueBooks.length,
            page: parseInt(page),
            totalPages: Math.ceil(uniqueBooks.length / limit)
        });
    } catch (error) {
        console.error('Get offline books error:', error);
        res.status(500).json({ error: 'Ошибка получения книг для оффлайн-режима' });
    }
});

// Сохранение оффлайн-прогресса
app.post('/api/offline/sync', authenticateToken, async (req, res) => {
    try {
        const { progressUpdates, newQuotes, newReviews } = req.body;
        
        // Синхронизация прогресса чтения
        if (progressUpdates && Array.isArray(progressUpdates)) {
            for (const update of progressUpdates) {
                await ReadingProgress.findOneAndUpdate(
                    {
                        userId: req.user.userId,
                        bookId: update.bookId
                    },
                    {
                        currentPage: update.currentPage,
                        lastReadAt: new Date(update.lastReadAt),
                        completed: update.completed,
                        completedAt: update.completed ? new Date() : null
                    },
                    { upsert: true }
                );
            }
        }

        // Синхронизация цитат
        if (newQuotes && Array.isArray(newQuotes)) {
            for (const quote of newQuotes) {
                await Quote.create({
                    ...quote,
                    userId: req.user.userId,
                    createdAt: new Date(quote.createdAt)
                });
            }
        }

        // Синхронизация рецензий
        if (newReviews && Array.isArray(newReviews)) {
            for (const review of newReviews) {
                await Review.create({
                    ...review,
                    userId: req.user.userId,
                    createdAt: new Date(review.createdAt)
                });
            }
        }

        // Обновление статистики пользователя
        await updateUserReadingStats(req.user.userId);

        res.json({ message: 'Данные успешно синхронизированы' });
    } catch (error) {
        console.error('Sync offline data error:', error);
        res.status(500).json({ error: 'Ошибка синхронизации данных' });
    }
});

// ==================== РОУТЫ КРОСС-ПЛАТФОРМЕННОЙ СИНХРОНИЗАЦИИ ====================

// Получение токена синхронизации
app.post('/api/sync/token', authenticateToken, async (req, res) => {
    try {
        const syncToken = jwt.sign(
            { userId: req.user.userId, type: 'sync' },
            process.env.JWT_SECRET,
            { expiresIn: '1h' }
        );

        res.json({ syncToken });
    } catch (error) {
        console.error('Generate sync token error:', error);
        res.status(500).json({ error: 'Ошибка генерации токена синхронизации' });
    }
});

// Проверка изменений (для оптимистичной синхронизации)
app.get('/api/sync/changes', authenticateToken, async (req, res) => {
    try {
        const { lastSync } = req.query;
        const lastSyncDate = lastSync ? new Date(lastSync) : new Date(0);

        const [progressChanges, quoteChanges, reviewChanges] = await Promise.all([
            ReadingProgress.find({
                userId: req.user.userId,
                updatedAt: { $gt: lastSyncDate }
            }).select('bookId currentPage completed updatedAt'),
            
            Quote.find({
                userId: req.user.userId,
                updatedAt: { $gt: lastSyncDate }
            }).select('bookId text page createdAt updatedAt'),
            
            Review.find({
                userId: req.user.userId,
                updatedAt: { $gt: lastSyncDate }
            }).select('bookId rating text createdAt updatedAt')
        ]);

        res.json({
            progress: progressChanges,
            quotes: quoteChanges,
            reviews: reviewChanges,
            serverTime: new Date().toISOString()
        });
    } catch (error) {
        console.error('Get sync changes error:', error);
        res.status(500).json({ error: 'Ошибшибка получения изменений' });
    }
});

// ==================== РОУТЫ ГРУПП И СООБЩЕСТВ ====================

// Создание группы
app.post('/api/groups', authenticateToken, async (req, res) => {
    try {
        const { name, description, isPrivate } = req.body;
        
        const group = new Group({
            name,
            description,
            isPrivate,
            createdBy: req.user.userId,
            members: [req.user.userId],
            admins: [req.user.userId]
        });

        await group.save();

        res.status(201).json({ group });
    } catch (error) {
        console.error('Create group error:', error);
        res.status(500).json({ error: 'Ошибка создания группы' });
    }
});

// Поиск групп
app.get('/api/groups/search', authenticateToken, async (req, res) => {
    try {
        const { query, page = 1, limit = 20 } = req.query;
        const skip = (page - 1) * limit;

        const searchQuery = query ? {
            $or: [
                { name: new RegExp(query, 'i') },
                { description: new RegExp(query, 'i') }
            ],
            $or: [
                { isPrivate: false },
                { members: req.user.userId }
            ]
        } : {
            $or: [
                { isPrivate: false },
                { members: req.user.userId }
            ]
        };

        const groups = await Group.find(searchQuery)
            .populate('createdBy', 'username avatar')
            .populate('members', 'username avatar')
            .skip(skip)
            .limit(parseInt(limit))
            .sort({ createdAt: -1 });

        const total = await Group.countDocuments(searchQuery);

        res.json({
            groups,
            total,
            page: parseInt(page),
            totalPages: Math.ceil(total / limit)
        });
    } catch (error) {
        console.error('Search groups error:', error);
        res.status(500).json({ error: 'Ошибка поиска групп' });
    }
});

// Обсуждение книги в группе
app.post('/api/groups/:groupId/discussions', authenticateToken, async (req, res) => {
    try {
        const { bookId, title, message } = req.body;
        
        const group = await Group.findById(req.params.groupId);
        
        if (!group) {
            return res.status(404).json({ error: 'Группа не найдена' });
        }

        // Проверка членства в группе
        if (!group.members.includes(req.user.userId)) {
            return res.status(403).json({ error: 'Вы не являетесь участником группы' });
        }

        const discussion = new Discussion({
            groupId: req.params.groupId,
            bookId,
            title,
            createdBy: req.user.userId,
            messages: [{
                userId: req.user.userId,
                message,
                createdAt: new Date()
            }]
        });

        await discussion.save();

        // Добавление в активность группы
        group.recentActivity.push({
            type: 'discussion_started',
            userId: req.user.userId,
            discussionId: discussion._id,
            createdAt: new Date()
        });

        await group.save();

        res.status(201).json({ discussion });
    } catch (error) {
        console.error('Create discussion error:', error);
        res.status(500).json({ error: 'Ошибка создания обсуждения' });
    }
});

// ==================== РОУТЫ ЧИТАТЕЛЬСКИХ ВЫЗОВОВ ====================

// Получение активных читательских вызовов
app.get('/api/challenges', async (req, res) => {
    try {
        const now = new Date();
        
        const challenges = await Challenge.find({
            startDate: { $lte: now },
            endDate: { $gte: now },
            isActive: true
        })
        .populate('createdBy', 'username avatar')
        .sort({ createdAt: -1 });

        res.json({ challenges });
    } catch (error) {
        console.error('Get challenges error:', error);
        res.status(500).json({ error: ' 'Ошибка получения вызовов' });
    }
});

// Участие в вызове
app.post('/api/challenges/:challengeId/join', authenticateToken, async (req, res) => {
    try {
        const challenge = await Challenge.findById(req.params.challengeId);
        
        if (!challenge) {
            return res.status(404).json({ error: 'Вызов не найден' });
        }

        // Проверка срока действия
        const now = new Date();
        if (now < challenge.startDate || now > challenge.endDate) {
            return res.status(400).json({ error: 'Вызов не активен' });
        }

        // Проверка уже ли участвует
        const existingParticipation = await ChallengeParticipation.findOne({
            challengeId: req.params.challengeId,
            userId: req.user.userId
        });

        if (existingParticipation) {
            return res.status(400).json({ error: 'Вы уже участвуете в этом вызове' });
        }

        const participation = new ChallengeParticipation({
            challengeId: req.params.challengeId,
            userId: req.user.userId,
            joinedAt: new Date(),
            progress: 0
        });

        await participation.save();

        // Добавление в активность
        const activity = new Activity({
            userId: req.user.userId,
            type: 'challenge_joined',
            data: { 
                challengeName: challenge.name,
                challengeId: challenge._id 
            }
        });
        await activity.save();

        res.json({ 
            message: 'Вы успешно присоединились к вызову',
            participation 
        });
    } catch (error) {
        console.error('Join challenge error:', error);
        res.status(500).json({ error: 'Ошибка присоединения к вызову' });
    }
});

// ==================== РОУТЫ АНАЛИТИКИ И ОТЧЕТОВ ====================

// Генерация ежемесячного отчета
app.get('/api/analytics/monthly-report', authenticateToken, async (req, res) => {
    try {
        const { year, month } = req.query;
        const targetDate = new Date(year, month - 1, 1);
        
        const startOfMonth = new Date(targetDate.getFullYear(), targetDate.getMonth(), 1);
        const endOfMonth = new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0);

        const [
            booksRead,
            pagesRead,
            readingTime,
            favoriteGenres,
            readingPatterns
        ] = await Promise.all([
            // Книги прочитанные за месяц
            ReadingProgress.find({
                userId: req.user.userId,
                completed: true,
                completedAt: {
                    $gte: startOfMonth,
                    $lte: endOfMonth
                }
            })
            .populate('bookId', 'title author genre pages')
            .lean(),

            // Всего страниц прочитано
            ReadingProgress.aggregate([
                {
                    $match: {
                        userId: mongoose.Types.ObjectId(req.user.userId),
                        lastReadAt: {
                            $gte: startOfMonth,
                            $lte: endOfMonth
                        }
                    }
                },
                {
                    $group: {
                        _id: null,
                        totalPages: { $sum: '$pagesRead' }
                    }
                }
            ]),

            // Время чтения
            ReadingProgress.aggregate([
                {
                    $match: {
                        userId: mongoose.Types.ObjectId(req.user.userId),
                        lastReadAt: {
                            $gte: startOfMonth,
                            $lte: endOfMonth
                        }
                    }
                },
                {
                    $group: {
                        _id: null,
                        totalMinutes: { $sum: '$readingTime' }
                    }
                }
            ]),

            // Любимые жанры месяца
            ReadingProgress.aggregate([
                {
                    $match: {
                        userId: mongoose.Types.ObjectId(req.user.userId),
                        completed: true,
,
                        completedAt: {
                            $gte: startOfMonth,
                            $lte: endOfMonth
                        }
                    }
                },
                {
                    $lookup: {
                        from: 'books',
                        localField: 'bookId',
                        foreignField: '_id',
                        as: 'book'
                    }
                },
                { $unwind: '$book' },
                { $unwind: '$book.genre' },
                {
                    $group: {
                        _id: '$book.genre',
                        count: { $sum: 1 }
                    }
                },
                { $sort: { count: -1 } },
                { $limit: 5 }
            ]),

            // Паттерны чтения по дням недели
            ReadingProgress.aggregate([
                {
                    $match: {
                        userId: mongoose.Types.ObjectId(req.user.userId),
                        lastReadAt: {
                            $gte: startOfMonth,
                            $lte: endOfMonth
                        }
                    }
                },
                {
                    $group: {
                        _id: { $dayOfWeek: '$lastReadAt' },
 },
                        count: { $sum: 1 },
                        totalMinutes: { $sum: '$readingTime' }
                    }
                },
                { $sort: { '_id': 1 } }
            ])
        ]);

        const report = {
            period: `${month}/${year}`,
            summary: {
                booksRead: booksRead.length,
                pagesRead: pagesRead[0]?.totalPages || 0,
                readingTime: {
                    minutes: readingTime[0]?.totalMinutes || 0,
                    hours: Math.round((readingTime[0]?.totalMinutes || 0) / 60 * 10) / 10
                },
                averagePerDay: {
                    pages: Math.round((pagesRead[0]?.totalPages || 0) / 30 * 10) / 10,
                    minutes: Math.round((readingTime[0]?.totalMinutes || 0) / 30 * 10) / 10
                }
            },
            books: booksRead.map(progress => ({
                title: progress.bookId.title,
                author: progress.bookId.author,
                genre: progress.bookId.genre,
                pages: progress.bookId.pages,
                completedAt: progress.completedAt
            })),
            favoriteGenres: favoriteGenres.map(genre => ({
                genre: genre._id,
                booksCount: genre.count
            })),
            readingPatterns: readingPatterns.map(pattern => ({
                dayOfWeek: pattern._id,
                readingSessions: pattern.count,
                totalMinutes: pattern.totalMinutes
            })),
            achievements: await getUserAchievements(req.user.userId, startOfMonth, endOfMonth)
        };

        res.json({ report });
    } catch (error) {
        console.error('Generate monthly report error:', error);
        res.status(500).json({ error: 'Ошибка генерации отчета' });
    }
});

// ==================== ВСПОМОГАТАТЕЛЬНЫЕ ФУНКЦИИ ====================

// Обновление статистики пользователя
async function updateUserReadingStats(userId) {
    const user = await User.findById(userId);
    
    const stats = await ReadingProgress.aggregate([
        {
            $match: { userId: mongoose.Types.ObjectId(userId) }
        },
        {
            $group: {
                _id: null,
                totalBooks: { $sum: { $cond: ['$completed', 1, 0] } },
                totalPages: { $sum: '$pagesRead' },
                totalTime: { $sum: '$readingTime' }
            }
        }
    ]);

    if (stats.length > 0) {
        user.readingStats.booksRead = stats[0].totalBooks;
        user.readingStats.pagesRead = stats[0].totalPages;
        user.readingStats.readingTime = stats[0].totalTime;
        await user.save();
    }
}

// Получение достижений пользователя
async function getUserAchievements(userId, startDate, endDate) {
    const achievements = [];
    
    // Проверка достижений
    const monthlyProgress = await ReadingProgress.countDocuments({
        userId,
        completed: true,
        completedAt: { $gte: startDate, $lte: endDate }
    });

    if (monthlyProgress >= 10) {
        achievements.push({
            name: 'Запойный читатель',
            description: 'Прочитать 1010 книг за месяц',
            icon: '📚',
            unlockedAt: new Date()
        });
    }

    const streak = await calculateCurrentStreak(userId);
    if (streak >= 30) {
        achievements.push({
            name: 'Железная воля',
            description: '30 дней подряд читать каждый день',
            icon: '🔥',
            unlockedAt: new Date()
        });
    }

    return achievements;
}

// Расчет текущего стрика
async function calculateCurrentStreak(userId) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    let streak = 0;
    let currentDate = today;
    
    while (true) {
        const startOfDay = new Date(currentDate);
        const endOfDay = new Date(currentDate);
        endOfDay.setHours(23, 59, 59, 999);
        
        const hasRead = await ReadingProgress.exists({
            userId,
            last lastReadAt: { $gte: startOfDay, $lte: endOfDay }
        });
        
        if (hasRead) {
            streak++;
            currentDate.setDate(currentDate.getDate() - 1);
        } else {
            break;
        }
    }
    
    return streak;
}

// ==================== МОДЕЛИ ДАННЫХ ====================

// Модель группы (добавить в существующие модели)
const groupSchema = new mongoose.Schema({
    name: { type: String, required: true },
    description: String,
    isPrivate: { type: Boolean, default: false },
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    members: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    admins: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    avatar: String,
    banner: String,
    rules: [String],
    recentActivity: [{
        type: { type: String, enum: ['discussion_started', 'book_added', 'event_created'] },
        userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
        discussionId: { type: mongoose.Schema.Types.ObjectId, ref: 'Discussion' },
        bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book' },
        createdAt: Date
    }],
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
});

// Модель обсуждения
const discussionSchema = new mongoose.Schema({
    groupId: { type: mongoose.Schema.Types.ObjectId, ref: 'Group', required: true },
    bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book' },
    title: { type: String, required: true },
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    messages: [{
        userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
        message: { type: String, required: true },
        createdAt: { type: Date, default: Date.now },
        likes: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }]
    }],
    isPinned: { type: Boolean, default: false },
    isClosed: { type: Boolean, default: false },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
});

// Модель читательского вызова
const challengeSchema = new mongoose.Schema({
    name: { type: String, required: true },
    description: String,
    type: { 
        type: String, 
        enum: ['books_count', 'pages_count', 'genre_specific', 'time_based'],
        required: true 
    },
    goal: { type: Number, required: true }, // например, 10 книг или 1000 страниц
    criteria: mongoose.Schema.Types.Mixed, // дополнительные критерии
    startDate: { type: Date, required: true },
    endDate: { type: Date, required: true },
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    participants: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    isActive: { type: Boolean, default: true },
    badgeIcon: String,
    createdAt: { type: Date, default: Date.now }
});

// Модель участия в вызове
const challengeParticipationSchema = new mongoose.Schema({
    challengeId: { type: mongoose.Schema.Types.ObjectId, ref: 'Challenge', required: true },
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    joinedAt: { type: Date, default: Date.now },
    progress: { type: Number, default: 0 },
    completed: { type: Boolean, default: false },
    completedAt: Date,
    updatedAt: { type: Date, default: Date.now }
});

// Модель прогресса аудиокниги
const audioProgressSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book', required: true },
    currentTime: { type: Number, default: 0 }, // текущее время в секундах
    duration: { type: Number, default: 0 }, // общая длительность в секундах
    chapter: { type: Number, default: 1 },
    lastListenedAt: { type: Date, default: Date.now },
    completed: { type: Boolean, default: false },
    completedAt: Date
});

// Создание моделей
const Group = mongoose.model('Group', groupSchema);
const Discussion = mongoose.model('Discussion', discussionSchema);
const Challenge = mongoose.model('Challenge', challengeSchema);
const ChallengeParticipation = mongoose.model('ChallengeParticipation', challengeParticipationSchema);
const AudioProgress = mongoose.model('AudioProgress', audioProgressSchema);

// ==================== КОНФИГУРАЦИЯ И ОПТИМИЗАЦИЯ ====================

// Добавление индексов для производительности
async function createIndexes() {
    await ReadingProgress.createIndexes([
        { userId: 1, bookId: 1 },
        { userId: 1, completed: 1, completedAt: 1 },
        { userId: 1, lastReadAt: 1 }
    ]);
    
    await User.createIndexes([
        { email: 1 },
        { username: 1 },
        { 'readingStats.booksRead': -1 }
    ]);
    
    await Book.createIndexes([
        { title: 'text', author: 'text', description: 'text' },
        { genre: 1 },
        { 'rating.average': -1 }
    ]);
    
    await Activity.createIndexes([
        { userId: 1, createdAt: -1 },
        { type: 1, createdAt: -1 }
    ]);
    
    await Group.createIndexes([
        { name: 'text', description: 'text' },
        { members: 1 },
        { createdAt: -1 }
    ]);
}

// Инициализация индексов при запуске
createIndexes().catch(console.error);

// ==================== ЗАПУСК СЕРВЕРА ====================

const server = app.listen(PORT, () => {
    console.log(`🚀 Сервер запущен на порту ${PORT}`);
    console.log(`📚 API доступен по адресу: http://localhost:${PORT}`);
    console.log(`📊 MongoDB подключена: ${process.env.MONGODB_URI}`);
    console.log(`🔄 Режим: ${process.env.NODE_ENV || 'development'}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 Получен SIGTERM. Завершение работы...');
    server.close(() => {
        console.log('✅ Сервер остановлен');
        mongoose.connection.close(false, () => {
            console.log('✅ MongoDB соединение закрыто');
            process.exit(0);
        });
    });
});

// Экспорт для тестирования
module.exports = { app, server };
