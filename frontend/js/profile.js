import { api } from "./api.js";
import { router } from "./app.js";

await update_userinfo()

document.getElementById("back").addEventListener("click", async (e) => {
  history.back();
});

document.getElementById("upload-photo").addEventListener("change", async (e) => {
  let photo = document.getElementById("upload-photo").files[0];
  let formData = new FormData();
      
  formData.append("profile_picture", photo);
  await fetch('/api/profile/', {method: "PATCH", body: formData});
  
  await update_userinfo();
});

document.getElementById("content").addEventListener('click', async function (event) {
  const target = event.target;
  const form = target.closest('form');
  
  if (!form) return;
  if (form.id == "picture") return;
  
  const editBtn = form.querySelector('.edit-button');
  const confirmBtn = form.querySelector('.confirm-button');
  const cancelBtn = form.querySelector('.cancel-button');

  if (target.closest('.edit-button')) {
    form.classList.add('editing');
    editBtn.style.display = 'none';
    confirmBtn.style.display = 'inline-block';
    cancelBtn.style.display = 'inline-block';
    form.querySelector('input').disabled = false;
    form.querySelector('input').readOnly = false;
  } else if (target.closest('.confirm-button')) {
    if (form.querySelector('input').id == "displayname") {
      const result = await api.patch("/profile/", {
        displayname: form.querySelector('input').value,
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
    if (form.querySelector('input').id == "email") {
      const result = await api.patch("/profile/", {
        email: form.querySelector('input').value,
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
      (await result.json());
    }
    resetButtons(form, editBtn, confirmBtn, cancelBtn);
  } else if (target.closest('.cancel-button')) {
    resetButtons(form, editBtn, confirmBtn, cancelBtn);
  }
  await update_userinfo()
});

document.getElementById("delete").addEventListener('click', async function (event) {
  const result = await api.delete("/profile/");
  router.navigate("/home")
  event.preventDefault();
});

function showAlert(message) {
  const alertContainer = document.getElementById('alertContainer');
  
  const alertElement = document.createElement('div');
  alertElement.classList.add('alert', 'alert-danger', 'alert-dismissible', 'fade', 'show');
  alertElement.setAttribute('role', 'alert');
  
  alertElement.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  alertContainer.appendChild(alertElement);
  
  // Initialize the Bootstrap alert
  new bootstrap.Alert(alertElement);
}

function resetButtons(form, editBtn, confirmBtn, cancelBtn) {
  form.querySelector('input').disabled = true;
  form.querySelector('input').readOnly = true;
  form.classList.remove('editing');
  editBtn.style.display = 'inline-block';
  confirmBtn.style.display = 'none';
  cancelBtn.style.display = 'none';
}

async function update_userinfo() {
  const result = await api.get("/profile/");
  const profile_info = await result.json()

  const photo = document.getElementById("profile-photo");
  photo.src = profile_info["profile_picture"];

  document.getElementById('displayname').value = profile_info["displayname"];

  const email = document.getElementById("email");
  email.value = profile_info["email"];
}