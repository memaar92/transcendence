import { api } from "./api.js";
import { router } from "./app.js";

const result = await api.get("/games/");
const games = await result.json();

document.getElementById("back").addEventListener("click", async (e) => {
  router.navigate("/main_menu");
});

async function tableCreate() {
  const table = document.getElementById("matchDataBody");
  if (!table) return;
  const myId = await getMyId();

  if (games.length == 0) {
    let row = table.insertRow();
    let cell = row.insertCell();
    cell.textContent = "No games Found";
    cell.colSpan = 5;
  }
  
  const gameDisp = document.getElementById("games");
  if (!gameDisp) return;
  gameDisp.textContent = games.length

  let wins = 0;
  let losses = 0;

  for (let i = 0; i < games.length; i++) {
    let row = table.insertRow();
    row.insertCell(0).textContent = i + 1;
    row.insertCell(1).textContent = await getUsername(myId);
    if (games[i]["home_id"] == myId) {
      if (games[i]["visitor_id"] == null) {
        row.insertCell(2).textContent = "[deleted]";
      } else {
        row.insertCell(2).textContent = await getUsername(games[i]["visitor_id"]);
      }
      row.insertCell(
        3
      ).textContent = `${games[i]["home_score"]} - ${games[i]["visitor_score"]}`;
      if (games[i]["home_score"] > games[i]["visitor_score"])
        wins++;
      else if (games[i]["home_score"] < games[i]["visitor_score"])
        losses++;
    } else {
        if (games[i]["home_id"] == null) {
            row.insertCell(2).textContent = "[deleted]";
        } else {
            row.insertCell(2).textContent = await getUsername(games[i]["home_id"]);
        }
      row.insertCell(
        3
      ).textContent = `${games[i]["visitor_score"]} - ${games[i]["home_score"]}`;
      if (games[i]["visitor_score"] > games[i]["home_score"])
        wins++;
      else if (games[i]["visitor_score"] < games[i]["home_score"])
        losses++;
    }
    let date = new Date(games[i]["created_at"]);
    row.insertCell(4).textContent = date.toLocaleString("en-US");
  }
  const winDisp = document.getElementById("wins");
  if (!winDisp) return;
  winDisp.textContent = wins

  const lossDisp = document.getElementById("losses");
  if (!lossDisp) return;
  lossDisp.textContent = losses;
}

await tableCreate();

async function getUsername(id) {
  const result = await api.get(`/users/${id}/`);
  const info = await result.json();
  return info["displayname"];
}

async function getMyId() {
  const result = await api.get(`/profile/`);
  const info = await result.json();
  return info["id"];
}
