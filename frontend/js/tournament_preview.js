import { api } from "./api.js";
import { router } from "./app.js";
import { hubSocket } from "./app.js";

function game_start(message) {
    if (message.type == "remote_match_ready")
    {
        window.localStorage.setItem("game_id", message.match_id)
        router.navigate("/game")
    }
}

document.getElementById("back").addEventListener("click", async (e) => {
  router.navigate("/main_menu");
});

hubSocket.registerCallback(game_start);

function checkFlag() {
  if(!localStorage.getItem("tournament_games")) {
     window.setTimeout(checkFlag, 100);
  } else {
  }
}
checkFlag();

const playerID = api.get("/profile/");

const tournament_name = localStorage.getItem("tournament_name");
console.log(tournament_name);
document.getElementById("name").innerHTML = tournament_name;
const tournament_data = localStorage.getItem("tournament_games");
console.log(tournament_data);
const tournament_json = JSON.parse(tournament_data);
console.log(tournament_json);

for (const row of tournament_json) {
    row[0] = await getUsername(row[0]);
    row[1] = await getUsername(row[1]);
}

if (window.location.pathname == "/tournament_preview")
  createTable(tournament_json)

async function getUsername(id) {
  const result = await api.get(`/users/${id}/`);
  const info = await result.json();
  return info["displayname"];
}

function createTable(tableData) {
    var tableBody = document.getElementById('scores');
    tableData.forEach(function(rowData, index) {
      var row = document.createElement('tr');
      console.log(rowData)
      rowData.unshift(index + 1)
  
      rowData.forEach(function(cellData) {
        var cell = document.createElement('td');
        cell.appendChild(document.createTextNode(cellData));
        row.appendChild(cell);
      });
  
      tableBody.appendChild(row);
    });
  }