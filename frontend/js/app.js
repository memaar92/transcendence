import Router from './router.js';

const routes = [
  { path: '/', templateUrl: '/routes/home.html' },
  { path: '/home', templateUrl: '/routes/home.html' },
  { path: '/email_verification', templateUrl: '/routes/email_verification.html' },
  { path: '/login', templateUrl: '/routes/login.html' },
  { path: '/register', templateUrl: '/routes/register.html' },
  { path: '/main_menu', templateUrl: '/routes/main_menu.html' },
  { path: '/404', templateUrl: '/routes/404.html' },
  { path: '/game_menu', templateUrl: '/routes/game_menu.html' },
  { path: '/play', templateUrl: '/routes/play.html' },
  { path: '/live_chat', templateUrl: '/routes/chat.html' },
  { path: '/game', templateUrl: '/routes/game.html' },
];

const router = new Router(routes);

/* chat handler */
document.addEventListener('DOMContentLoaded', () => {
  router.init(document.getElementById('app'));
  console.log('App started');
  console.log('Current path:', window.location.pathname);
  if (window.location.pathname === '/live_chat') {
    console.log('Initializing chat');
    const authToken = localStorage.getItem('authToken');
    if (authToken) {
      ChatHandler.getInstance().init(authToken);
    } else {
      console.error('No auth token found in localStorage');
    }
  }
});
