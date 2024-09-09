import { api } from "./api.js";
import { router } from "./app.js";

const result = await api.get("/games/");
const games = await result.json();
const profile_info = await result.json()

const photo = document.getElementById("profile-photo");
photo.src = profile_info["profile_picture"];

document.getElementById('displayname').value = profile_info["displayname"];

const email = document.getElementById("email");
email.value = profile_info["email"];

document.getElementById("back").addEventListener("click", async (e) => {
  console.log("going back");
  history.back();
});

function tableCreate() {
    const content = document.getElementById("content"),
          tbl = document.createElement('table');
    tbl.style.width = '100px';
    tbl.style.border = '1px solid white';
    console.log("MAKING TABLE")
    console.log(content)
  
    for (let i = 0; i < 3; i++) {
      const tr = tbl.insertRow();
      for (let j = 0; j < 2; j++) {
        if (i === 2 && j === 1) {
          break;
        } else {
          const td = tr.insertCell();
          td.appendChild(document.createTextNode(`Cell I${i}/J${j}`));
          td.style.border = '1px solid white';
          if (i === 1 && j === 1) {
            td.setAttribute('rowSpan', '2');
          }
        }
      }
    }
    content.appendChild(tbl);
  }
  
tableCreate();

async function getUsername(id) {
    const result = await api.get(`/users/${id}`);
    const games = await result.json();
}