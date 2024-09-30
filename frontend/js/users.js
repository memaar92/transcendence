import { api } from "./api.js";
import { router } from "./app.js";

const result = await api.get(`/users/${localStorage.getItem("UID")}`);
const profile_info = await result.json()

document.getElementById("profile-photo").src = profile_info["profile_picture"];
document.getElementById('displayname').innerText = profile_info["displayname"];


const games_html = await api.get("/games/");
const games = await games_html.json();

(games);

document.getElementById("back").addEventListener("click", async (e) => {
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
  const result = await api.get(`/profile/`);
  const info = await result.json();
  return info["id"];
}

async function getUsersRelationship() {
  const myId = await getMyId();
  const result = await api.get(`/chat/users/relationships/${myId}/${localStorage.getItem("UID")}/`);
  if (result.status == 400) {
    return null;
  }
  const info = await result.json();
  return info["relationship"]["fields"];
}

async function createProfileButton() {
  const myId = await getMyId();
  const relationship = await getUsersRelationship();
  const profileContainer = document.getElementById("user-content");
  const buttonContainer = document.createElement("div");
  var button = document.createElement("button");
  button.classList.add("button");

  console.log(relationship);
  if (relationship && relationship["status"]) {
    if (relationship["status"] == "BF") {
      button.textContent = "Unfriend";
      button.addEventListener("click", cancelFriendRequest);
      buttonContainer.appendChild(button);
      button = document.createElement("button");
      button.classList.add("button");
      button.textContent = "Block";
      button.addEventListener("click", blockFriend);
    } else if (relationship["status"] == "PD") {
      if (relationship["requester"] == myId) {
        button.textContent = "Cancel Request";
        button.addEventListener("click", cancelFriendRequest);
      }
      else
      {
        button.textContent = "Accept Request";
        button.addEventListener("click", acceptFriendRequest);
        buttonContainer.appendChild(button);
        button = document.createElement("button");
        button.classList.add("button");
        button.textContent = "Decline Request";
        button.addEventListener("click", cancelFriendRequest);
      }
    } else if (relationship["status"] == "BL") {
      button.textContent = "Blocked";
    } else {
      button.textContent = "Add Friend";
      button.addEventListener("click", makeFriendRequest);
    }
  } else {
    button.textContent = "Add Friend";
    button.addEventListener("click", makeFriendRequest);
  }

  buttonContainer.appendChild(button);

  const profilePhoto = document.getElementById("profile-photo");
  profileContainer.insertBefore(buttonContainer, profilePhoto.nextSibling);
}

await createProfileButton();

async function makeFriendRequest() {
  const myId = await getMyId();
  const result = await api.patch(`/chat/users/relationships/${myId}/${localStorage.getItem("UID")}/`, {
    status: "PD",
    requester: myId,
  });
  if (result.status == 400)
  {
    await result.json()
      .then(data => {
        if (data.errors) {
          showAlert(JSON.stringify(data.errors));
        } else {
          showAlert('No errors found');
        }
      })
      .catch(error => {
        showAlert(`Error parsing JSON: ${error.message}`);
      });
  }
}

async function cancelFriendRequest() {
  const myId = await getMyId();
  const result = await api.patch(`/chat/users/relationships/${myId}/${localStorage.getItem("UID")}/`, {
    status: "DF",
    requester: null,
  });
  if (result.status == 400)
  {
    await result.json()
      .then(data => {
        if (data.errors) {
          showAlert(JSON.stringify(data.errors));
        } else {
          showAlert('No errors found');
        }
      })
      .catch(error => {
        showAlert(`Error parsing JSON: ${error.message}`);
      });
  }
}

async function acceptFriendRequest() {
  const myId = await getMyId();
  const result = await api.patch(`/chat/users/relationships/${myId}/${localStorage.getItem("UID")}/`, {
    status: "BF",
    requester: null,
  });
  if (result.status == 400)
  {
    await result.json()
      .then(data => {
        if (data.errors) {
          showAlert(JSON.stringify(data.errors));
        } else {
          showAlert('No errors found');
        }
      })
      .catch(error => {
        showAlert(`Error parsing JSON: ${error.message}`);
      });
  }
}

async function blockFriend() {
  const myId = await getMyId();
  const result = await api.patch(`/chat/users/relationships/${myId}/${localStorage.getItem("UID")}/`, {
    status: "BL",
    requester: null,
  });
  if (result.status == 400)
  {
    await result.json()
      .then(data => {
        if (data.errors) {
          showAlert(JSON.stringify(data.errors));
        } else {
          showAlert('No errors found');
        }
      })
      .catch(error => {
        showAlert(`Error parsing JSON: ${error.message}`);
      });
  }
}