import { api } from "./api.js";
import { router } from "./app.js";

const result = await api.get(`/users/${localStorage.getItem("UID")}`);
const profile_info = await result.json()

document.getElementById("profile-photo").src = profile_info["profile_picture"];
document.getElementById('displayname').innerText = profile_info["displayname"];


const games_html = await api.get("/games/");
const games = await games.json();

console.log(games);

document.getElementById("back").addEventListener("click", async (e) => {
  console.log("going back");
  history.back();
});

async function tableCreate() {
  const table = document.getElementById("matchDataBody");
  const myId = await getMyId();

  if (games.length == 0) {
    let row = table.insertRow();
    let cell = row.insertCell();
    cell.textContent = "No games Found";
    cell.colSpan = 5;
  }
  
  document.getElementById("games").textContent = games.length
  let wins = 0;
  let losses = 0;

  for (let i = 0; i < games.length; i++) {
    let row = table.insertRow();
    row.insertCell(0).textContent = i + 1;
    row.insertCell(1).textContent = await getUsername(myId);
    if (games[i]["home_id"] == myId) {
      row.insertCell(2).textContent = await getUsername(games[i]["visitor_id"]);
      row.insertCell(
        3
      ).textContent = `${games[i]["home_score"]} - ${games[i]["visitor_score"]}`;
      if (games[i]["home_score"] > games[i]["visitor_score"])
        wins++;
      else if (games[i]["home_score"] < games[i]["visitor_score"])
        losses++;
    } else {
      row.insertCell(2).textContent = await getUsername(games[i]["home_id"]);
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
  document.getElementById("wins").textContent = wins;
  document.getElementById("losses").textContent = losses;
}

await tableCreate();

async function getUsername(id) {
  const result = await api.get(`/users/${id}/`);
  const info = await result.json();
  return info["displayname"];
}

async function getMyId() {
  const result = await api.get(`/profile/${get}`);
  const info = await result.json();
  return info["id"];
}
