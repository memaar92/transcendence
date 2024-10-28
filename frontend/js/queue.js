import { hubSocket, showAlert } from "./app.js";
import { router } from "./app.js";

function game_start(message) {
  if (message.type == "remote_match_ready") {
    localStorage.removeItem("tournament_games");
    window.localStorage.setItem("game_id", message.match_id);
    router.navigate("/game");
  } else if (!message.queue_registered && message.message == "registered to match") {
    router.navigate("/game");
  } else if (!message.queue_registered && message.message) {
    showAlert(message.message);
    router.navigate("/main_menu");
  }
}

function leave_queue() {
  hubSocket.send(
    {
      type: "queue_unregister"
    }
  )
}

hubSocket.registerCallback(game_start);
hubSocket.send({ type: "queue_register" });


const leave = document.getElementById("leave-queue");

if (leave) {
  leave.addEventListener("click", leave_queue);
}