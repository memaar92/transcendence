import { api } from "./api.js";
import { hubSocket, router, showAlert } from "./app.js";

hubSocket.send({type: "local_match_create"})
