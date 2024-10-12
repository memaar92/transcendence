import { api } from "./api.js";
import { router } from "./app.js";

const playerID = api.get("/profile");
document.getElementById("back").addEventListener("click", async (e) => {
  router.navigate("/main_menu");
});

const tournament_name = localStorage.getItem("tournament_name");
localStorage.removeItem("tournament_games");
console.log(tournament_name);
const tournament_data = localStorage.getItem("tournament_result");
console.log(tournament_data);
const tournament_json = JSON.parse(tournament_data);
console.log(tournament_json);

document.getElementById("name").innerHTML = tournament_name;
const sorted_table = Object.keys(tournament_json).map((key) => [key, tournament_json[key]]).sort((a, b) =>  b[1] - a[1]);

const winnner = document.getElementById("winner");
winner.innerHTML = await getUsername(sorted_table[0][0]);
const looser = document.getElementById("looser");
looser.innerHTML = await getUsername(sorted_table[sorted_table.length - 1][0]);

console.log("Sorted table", sorted_table);
for (const row of sorted_table) {
    row[0] = await getUsername(row[0]);
}

createTable(sorted_table)

async function getUsername(id) {
  const result = await api.get(`/users/${id}/`);
  const info = await result.json();
  return info["displayname"];
}

function createTable(tableData) {
    var tableBody = document.getElementById('scores');
  
    tableData.forEach(function(rowData) {
      var row = document.createElement('tr');
      console.log(rowData)
  
      rowData.forEach(function(cellData) {
        var cell = document.createElement('td');
        cell.appendChild(document.createTextNode(cellData));
        row.appendChild(cell);
      });
  
      tableBody.appendChild(row);
    });
  }