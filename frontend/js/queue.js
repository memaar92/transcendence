import { hubSocket } from "./app.js";
import { router } from "./app.js";


function game_start(message) {
    if (message.type == "remote_match_ready")
    {
        window.localStorage.setItem("game_id", message.match_id)
        router.navigate("/game")
    }
}

hubSocket.registerCallback(game_start);

hubSocket.send({type: "queue_register"});