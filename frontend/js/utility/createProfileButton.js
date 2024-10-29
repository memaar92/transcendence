
import { api } from "../api.js";

async function getMyId() {
  const result = await api.get(`/profile/`);
  const info = await result.json();
  return info["id"];
}

async function getUsersRelationship() {
  const myId = await getMyId();
  const response = await api.get(`/chat/users/relationships/${myId}/${localStorage.getItem("UID")}/`);

  if (response && response.ok) {
    const info = await response.json();
    if (info["message"] === "Relationship does not exist") {
      return null;
    }
    return info["relationship"]["fields"];
  }
  else {
    return null;
  }
}

export async function createProfileButton() {
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

        const action = relationship["blocker"] === myId ? () => updateUserRelationship(myId, userId, "BF") : () => updateUserRelationship(myId, userId, "DF");
        button = relationship["blocker"] === myId ? createButton("Unblock", ["button"], action) : createButton("Unfriend", ["button"], action);
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