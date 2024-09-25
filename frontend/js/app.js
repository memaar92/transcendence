import Router from "./router.js";

const routes = [
  { path: "/", templateUrl: "/routes/home.html" },
  { path: "/home", templateUrl: "/routes/home.html" },
  {
    path: "/email_verification",
    templateUrl: "/routes/email_verification.html",
  },
  { path: "/login", templateUrl: "/routes/login.html" },
  { path: "/register", templateUrl: "/routes/register.html" },
  { path: "/main_menu", templateUrl: "/routes/main_menu.html" },
  { path: "/404", templateUrl: "/routes/404.html" },
  { path: "/game_menu", templateUrl: "/routes/game_menu.html" },
  { path: "/play", templateUrl: "/routes/play.html" },
  { path: "/game_local", templateUrl: "/routes/game_local.html" },
  { path: "/game", templateUrl: "/routes/game.html" },
  { path: "/account", templateUrl: "/routes/account.html" },
  { path: "/security", templateUrl: "/routes/security.html" },
  { path: "/appearance", templateUrl: "/routes/appearance.html" },
  { path: "/stats", templateUrl: "/routes/stats.html" },
  { path: "/verify_2fa", templateUrl: "/routes/verify_2fa.html" },
];

export const router = new Router(routes);

document.addEventListener("DOMContentLoaded", () => {
  router.init(document.getElementById("app"));
});
