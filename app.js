const API_BASE = 'http://localhost:8000';
const chatEl = document.getElementById('chat');
const inputEl = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');
const emailEl = document.getElementById('email');
const passwordEl = document.getElementById('password');
const btnRegister = document.getElementById('btnRegister');
const btnLogin = document.getElementById('btnLogin');
const btnLogout = document.getElementById('btnLogout');

let busy = false;
let sessionId = null;

function setAuthUI(isAuth){
  btnLogout.hidden = !isAuth;
  btnLogin.hidden = isAuth;
  btnRegister.hidden = isAuth;
  emailEl.disabled = isAuth;
  passwordEl.disabled = isAuth;
}

function pushMessage(text, cls){
  const div = document.createElement('div');
  div.className = 'message ' + cls;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function showTyping(){
  const el = document.createElement('div');
  el.id = 'typing';
  el.className = 'message msg-bot';
  el.textContent = 'бот печатает...';
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function hideTyping(){
  const el = document.getElementById('typing');
  if(el) el.remove();
}

function getToken(){ return localStorage.getItem('jwt') || null; }

async function register(){
  try{
    const res = await fetch(API_BASE + '/auth/register', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email: emailEl.value, password: passwordEl.value})
    });
    if(!res.ok) throw new Error('Регистрация не удалась');
    alert('Зарегистрированы. Войдите.');
  }catch(e){ alert(e.message); }
}

async function login(){
  try{
    const res = await fetch(API_BASE + '/auth/login', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email: emailEl.value, password: passwordEl.value})
    });
    if(!res.ok) throw new Error('Вход не удался');
    const data = await res.json();
    localStorage.setItem('jwt', data.access_token);
    setAuthUI(true);
    await createSession();
  }catch(e){ alert(e.message); }
}

async function logout(){
  localStorage.removeItem('jwt');
  sessionId = null;
  setAuthUI(false);
  chatEl.innerHTML = '';
}

async function createSession(){
  const token = getToken();
  if(!token) return;
  const res = await fetch(API_BASE + '/chat/session', {
    method:'POST',
    headers:{'Content-Type':'application/json', 'Authorization':'Bearer ' + token},
    body: JSON.stringify({title: 'session-' + Date.now()})
  });
  if(!res.ok) {console.error('session create failed'); return;}
  const data = await res.json();
  sessionId = data.id;
  // load history
  const h = await fetch(API_BASE + `/chat/history/${sessionId}`, {headers:{'Authorization':'Bearer ' + token}});
  if(h.ok){
    const hist = await h.json();
    chatEl.innerHTML = '';
    hist.messages.forEach(m => pushMessage(m.text, m.sender === 'user' ? 'msg-user' : 'msg-bot'));
  }
}

async function sendMessage(){
  if(busy) return;
  const text = inputEl.value.trim();
  if(!text) return alert('Введите сообщение');
  if(!sessionId) return alert('Создайте/войдите в сессии');
  pushMessage(text, 'msg-user');
  inputEl.value='';
  busy = true;
  sendBtn.disabled = true;
  showTyping();

  try{
    const token = getToken();
    // simulate delay for UX and then fetch
    await new Promise(r => setTimeout(r, 700));
    const res = await fetch(API_BASE + '/chat/message', {
      method:'POST',
      headers:{
        'Content-Type':'application/json',
        'Authorization':'Bearer ' + token
      },
      body: JSON.stringify({session_id: sessionId, text})
    });
    if(!res.ok) throw new Error('Ошибка сервера при отправке сообщения');
    const data = await res.json();
    hideTyping();
    pushMessage(data.reply, 'msg-bot');
  }catch(err){
    hideTyping();
    pushMessage('Ошибка: ' + err.message, 'msg-bot');
  }finally{
    busy = false;
    sendBtn.disabled = false;
  }
}

async function clearChat(){
  chatEl.innerHTML = '';
  // Необязательно чистить на сервере — можно создать новую сессию
  await createSession();
}

inputEl.addEventListener('keydown', (e) => {
  if(e.key === 'Enter') sendMessage();
});
sendBtn.addEventListener('click', sendMessage);
clearBtn.addEventListener('click', clearChat);
btnRegister.addEventListener('click', register);
btnLogin.addEventListener('click', login);
btnLogout.addEventListener('click', logout);

// On load: adjust UI
if(getToken()){ setAuthUI(true); createSession(); } else setAuthUI(false);
