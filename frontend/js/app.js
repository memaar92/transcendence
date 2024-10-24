import Router from "./router.js";
import HubSocket from "./hubSocket.js";

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
  { path: "/auth_failed", templateUrl: "/routes/auth_failed.html" },
  { path: "/game_menu", templateUrl: "/routes/game_menu.html" },
  { path: "/play", templateUrl: "/routes/play.html" },
  { path: "/live_chat", templateUrl: "/routes/chat.html" },
  { path: "/live_chat/chat_room", templateUrl: "/routes/chat_room.html" },
  { path: "/game_local", templateUrl: "/routes/game_local.html" },
  { path: "/game", templateUrl: "/routes/game.html" },
  { path: "/tournament", templateUrl: "/routes/tournament.html" },
  { path: "/tournament_review", templateUrl: "/routes/tournament_review.html" },
  { path: "/tournament_preview", templateUrl: "/routes/tournament_preview.html" },
  { path: "/account", templateUrl: "/routes/account.html" },
  { path: "/security", templateUrl: "/routes/security.html" },
  { path: "/stats", templateUrl: "/routes/stats.html" },
  { path: "/verify_2fa", templateUrl: "/routes/verify_2fa.html" },
  { path: "/queue", templateUrl: "/routes/queue.html" },
  { path: "/endscreen", templateUrl: "/routes/endscreen.html" },
];

console.log("app loaded");
export const hubSocket = new HubSocket();
export const router = new Router(routes);

document.addEventListener("DOMContentLoaded", () => {
  router.init(document.getElementById("app"));
  console.log("App started");
});

export function showAlert(message) {
  const alertContainer = document.getElementById("main_alert");
  
  const alertElement = document.createElement("div");
  alertElement.classList.add(
    "alert",
    "alert-danger",
    "alert-dismissible",
    "fade",
    "show"
  );
  alertElement.setAttribute("role", "alert");
  
  alertElement.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  alertContainer.appendChild(alertElement);
  new bootstrap.Alert(alertElement);
}
