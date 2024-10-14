import { api } from "./api.js";
import { hubSocket, showAlert } from "./app.js";
import { router } from "./app.js";

const user_data = await api.get("/profile/");
const json = await user_data.json();
const uid = json.id;

hubSocket.connect();

var intervalId = window.setInterval(function () {
  hubSocket.send({ type: "tournament_get_open" });
}, 500);

const messages = {
  open_tounaments_list: updateTournamentList,
  // "Tournament starting.": tournament_alert,
};

let tournaments = null;

function tournamentCallback(message) {
  console.log("tour: ", message);
  if (message.type == "open_tournaments_list") {
    updateTournamentList(message);
  } else if (message.type === "tournament_starting") {
    console.log("Tournament starting.");
  } else if (message.type === "match_in_progress") {
    console.log("Match in progress.");
    showReconnectButton(data.match_id); // Pass the correct match_id
  } else if (message.type === "tournament_canceled") {
    console.log("Tournament canceled.");
  } else if (message.type == "remote_match_ready") {
    localStorage.setItem("game_id", message.match_id);
    clearInterval(intervalId);
    router.navigate("/game");
  } else if (message.type == "tournament_schedule") {
    localStorage.setItem("tournament_games", JSON.stringify(message.matches));
    localStorage.setItem("tournament_name", message.tournament_name);
    router.navigate("/tournament_preview");
    clearInterval(intervalId);
    return;
  } else if (!message.tournamentCreated && message.message) {
    showAlert(message.message)
  }
}
hubSocket.registerCallback(tournamentCallback);

function updateTournamentList(message) {
  console.log(message.tournaments, tournaments);
  if (JSON.stringify(message.tournaments) == JSON.stringify(tournaments))
    return;

  tournaments = message.tournaments;
  const tournament_table = document.getElementById("tournament-table");

  const new_tournaments = document.createElement("tbody");
  new_tournaments.id = "tournament-table";

  tournaments.forEach(async (tournament) => {
    const userCount = tournament.users.length; // Number of users registered in the tournament
    const isOwner = tournament.is_owner; // Is the current user the owner of the tournament
    const canStart = isOwner && userCount >= 2; // At least 2 players required to start

    const row = new_tournaments.insertRow(0);
    row.className = "dlheader";
    let name = row.insertCell(0);
    let owner = row.insertCell(1);
    let players = row.insertCell(2);
    let actions = row.insertCell(3);

    name.innerHTML = tournament.name;
    owner.innerHTML = await getUsername(tournament.owner);
    console.log(tournament);
    players.innerHTML = userCount + " / " + tournament.max_players;
    if (isOwner) {
      actions.innerHTML = `
            <button class="button start-button" data-id="${tournament.id}"${
        canStart ? "" : "disabled"
      }>
              Start
            </button>
  
            <button id="cancel-tournament" class="button cancel-tournament" data-id="${
              tournament.id
            }">
              Cancel
            </button>`;
    } else {
      const in_tournament = tournament.users.includes(uid);
      actions.innerHTML = `
                <button class="button register-button" data-id="${
                  tournament.id
                }" ${in_tournament ? "disabled" : ""}>Register</button>
                <button class="button unregister-button" data-id="${
                  tournament.id
                }" ${in_tournament ? "" : "disabled"}>Unregister</button>
            `;
    }
    tournament_table.parentNode.replaceChild(new_tournaments, tournament_table);

    document.querySelectorAll(".register-button").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.target.disabled = true;
        hubSocket.send({
          type: "tournament_register",
          tournament_id: event.target.getAttribute("data-id"),
        });
      });
    });

    document.querySelectorAll(".unregister-button").forEach((button) => {
      button.addEventListener("click", (event) => {
        hubSocket.send({
          type: "tournament_unregister",
          tournament_id: event.target.getAttribute("data-id"),
        });
      });
    });

    document.querySelectorAll(".start-button").forEach((button) => {
      button.addEventListener("click", (event) => {
        hubSocket.send({
          type: "tournament_start",
          tournament_id: event.target.getAttribute("data-id"),
        });
      });
    });

    document.querySelectorAll(".cancel-tournament").forEach((button) => {
      button.addEventListener("click", (event) => {
        hubSocket.send({
          type: "tournament_cancel",
          tournament_id: event.target.getAttribute("data-id"),
        });
      });
    });
  });
}

const form = document.getElementById("tournament-form");
form.addEventListener("submit", (event) => {
  console.log("Submitted form");
  event.preventDefault(); // Prevent the form from submitting

  const name = document.getElementById("tournament-name").value;
  const maxPlayers = parseInt(document.getElementById("max-players").value, 10);
  console.log("Creating tournament:", name, maxPlayers);

  hubSocket.send({
    type: "tournament_create",
    name: name,
    max_players: maxPlayers,
  });
});

document.getElementById("back").addEventListener("click", async (e) => {
  clearInterval(intervalId);
  router.navigate("/main_menu");
});

async function getUsername(id) {
  const result = await api.get(`/users/${id}/`);
  const info = await result.json();
  return info["displayname"];
}
