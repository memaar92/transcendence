import { api } from "./api.js";
import { router } from "./app.js";

const result = await api.get(`/users/${localStorage.getItem("UID")}`);
const profile_info = await result.json()

document.getElementById("profile-photo").src = profile_info["profile_picture"];
document.getElementById('displayname').innerText = profile_info["displayname"];


const games_html = await api.get(`/users/${localStorage.getItem("UID")}/games`);
const games = await games_html.json();


document.getElementById("back").addEventListener("click", async (e) => {
  history.back();
});

async function tableCreate() {
  const table = document.getElementById("matchDataBody");
  const myId = localStorage.getItem("UID");

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
  document.getElementById("wins").textContent = wins;
  document.getElementById("losses").textContent = losses;
}

await createProfileButton();
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
  try {
    const response = await api.get(`/chat/users/relationships/${myId}/${localStorage.getItem("UID")}/`);

    if (!response.ok) {
      if (response.status === 400) {
        console.log("Relationship does not exist");
        return null;
      }
      throw new Error("Unexpected error");
    }

    const info = await response.json();
    return info["relationship"]["fields"];
  } catch (error) {
    console.warn("Error fetching relationship:", error);
    return null;
  }
}

async function createProfileButton() {
  const myId = await getMyId();
  const userId = localStorage.getItem("UID");
  const relationship = await getUsersRelationship();
  const buttonContainer = document.getElementById("buttonContainer");
  const profilePhoto = document.getElementById("profile-photo");

  // Reset profile photo styling
  profilePhoto.style.filter = "none";
  profilePhoto.style.opacity = "1";

  // Clear the button container before adding new buttons
  buttonContainer.innerHTML = "";

  // Helper function to create buttons
  function createButton(text, classes, action) {
    const button = document.createElement("button");
    button.textContent = text;
    button.classList.add("button", ...classes);
    button.addEventListener("click", async () => {
      await action();
      createProfileButton();
    });
    button.style.marginRight = "1rem";
    return button;
  }

  let button;

  if (relationship && relationship["status"]) {
    switch (relationship["status"]) {
      case "BF":
        button = createButton("Unfriend", ["button"], () => updateUserRelationship(myId, userId, "DF"));
        buttonContainer.appendChild(button);

        const blockButton = createButton("Block", ["dangerous-button"], () => updateUserRelationship(myId, userId, "BL"));
        buttonContainer.appendChild(blockButton);
        break;

      case "PD":
        if (relationship["requester"] === myId) {
          button = createButton("Cancel Request", ["button"], () => updateUserRelationship(myId, userId, "DF"));
        } else {
          button = createButton("Accept Request", ["button"], () => updateUserRelationship(myId, userId, "BF"));
          buttonContainer.appendChild(button);

          const declineButton = createButton("Decline Request", ["dangerous-button"], () => updateUserRelationship(myId, userId, "DF"));
          buttonContainer.appendChild(declineButton);
        }
        break;

      case "BL":
        profilePhoto.style.filter = "grayscale(100%)";
        profilePhoto.style.opacity = "0.5";

        const unblockAction = relationship["blocker"] === myId ? () => updateUserRelationship(myId, userId, "BF") : () => updateUserRelationship(myId, userId, "DF");
        button = createButton("Unblock", ["button"], unblockAction);
        break;

      default:
        button = createButton("Add Friend", ["button"], () => updateUserRelationship(myId, userId, "PD", myId));
        break;
    }
  } else {
    button = createButton("Add Friend", ["button"], () => updateUserRelationship(myId, userId, "PD", myId));
  }

  buttonContainer.appendChild(button);
}

async function updateUserRelationship(myId, userId, status)
{
  const result = await api.patch(`/chat/users/relationships/${myId}/${userId}/`, {
    status: status,
  });
  await checkHttpStatus(result);
}

async function checkHttpStatus(result){
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