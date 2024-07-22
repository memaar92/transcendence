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

document.addEventListener('DOMContentLoaded', () => {
  router.init(document.getElementById('app'));
});

