import { hubSocket, showAlert } from "./app.js";
import { router } from "./app.js";

function game_start(message) {
  if (message.type == "remote_match_ready") {
    window.localStorage.setItem("game_id", message.match_id);
    router.navigate("/game");
  } else if (!message.queue_registered && message.message) {
    showAlert(message.message);
    router.navigate("/main_menu");
  }
}

hubSocket.registerCallback(game_start);
hubSocket.send({ type: "queue_register" });
