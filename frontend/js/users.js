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
  const profileContainer = document.getElementById("user-content");
  const buttonContainer = document.createElement("div");
  var button = document.createElement("button");
  button.classList.add("button");

  if (relationship && relationship["status"]) {
    if (relationship["status"] == "BF") {
      button.textContent = "Unfriend";
      button.addEventListener("click", () => updateUserRelationship(myId, userId, "DF"));
      buttonContainer.appendChild(button);
      button = document.createElement("button");
      button.classList.add("button");
      button.textContent = "Block";
      button.addEventListener("click", () => updateUserRelationship(myId, userId, "BL"));
    } else if (relationship["status"] == "PD") {
      if (relationship["requester"] == myId) {
        button.textContent = "Cancel Request";
        button.addEventListener("click", () => updateUserRelationship(myId, userId, "DF"));
      } else {
        button.textContent = "Accept Request";
        button.addEventListener("click", () => updateUserRelationship(myId, userId, "BF"));
        buttonContainer.appendChild(button);
        button = document.createElement("button");
        button.classList.add("confirm-button");
        button.textContent = "Decline Request";
        button.addEventListener("click", () => updateUserRelationship(myId, userId, "DF"));
      }
    } else if (relationship["status"] == "BL") {
      if (relationship["blocker"] == myId) {
        button.textContent = "Unblock";
        button.addEventListener("click", () => updateUserRelationship(myId, userId, "BF"));
      }
      else {
        button.textContent = "Unfriend";
        button.addEventListener("click", () => updateUserRelationship(myId, userId, "DF"));
      }
      const profilePhoto = document.getElementById("profile-photo");
      const profilePhotoWrapper = document.getElementById("profile-photo-wrapper");
      
      // profilePhoto.style.filter = "grayscale(100%)";
      // profilePhoto.style.opacity = "0.5";
      profilePhoto.style.width = "256px";
      profilePhoto.style.height = "256px";
      
      const width = profilePhotoWrapper.clientWidth;
      const height = profilePhotoWrapper.clientHeight;
      
      const svgNS = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(svgNS, "svg");
      svg.setAttribute("width", width);
      svg.setAttribute("height", height);
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.style.position = "absolute";
      svg.style.top = "0";
      svg.style.left = "0";
      svg.style.zIndex = "1";
      
      const line1 = document.createElementNS(svgNS, "line");
      line1.setAttribute("x1", 20); // Starting x-coordinate
      line1.setAttribute("y1", 20); // Starting y-coordinate
      line1.setAttribute("x2", width - 20); // Ending x-coordinate
      line1.setAttribute("y2", height - 20); // Ending y-coordinate
      line1.setAttribute("stroke", "white");
      line1.setAttribute("stroke-width", "10");
      line1.setAttribute("stroke-linecap", "round");
      line1.setAttribute("stroke-opacity", "0.7");
      
      const line2 = document.createElementNS(svgNS, "line");
      line2.setAttribute("x1", width - 20); // Starting x-coordinate
      line2.setAttribute("y1", 20); // Starting y-coordinate
      line2.setAttribute("x2", 20); // Ending x-coordinate
      line2.setAttribute("y2", height - 20); // Ending y-coordinate
      line2.setAttribute("stroke", "white");
      line2.setAttribute("stroke-width", "10");
      line2.setAttribute("stroke-linecap", "round");
      line2.setAttribute("stroke-opacity", "0.7");
      
      svg.appendChild(line1);
      svg.appendChild(line2);
      
      profilePhotoWrapper.appendChild(svg);           
    } else {
      button.textContent = "Add Friend";
      button.addEventListener("click", () => updateUserRelationship(myId, userId, "PD", myId));
    }
  } else {
    button.textContent = "Add Friend";
    button.addEventListener("click", () => updateUserRelationship(myId, userId, "PD", myId));
  }

  buttonContainer.appendChild(button);

  const profilePhotoWrapper = document.getElementById("profile-photo-wrapper");
  profileContainer.insertBefore(buttonContainer, profilePhotoWrapper.nextSibling);
}

await createProfileButton();

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