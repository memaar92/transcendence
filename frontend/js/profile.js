import { api } from "./api.js";
import { router } from "./app.js";

const result = await api.get("/profile/");

const profile_info = await result.json()

const photo = document.getElementById("profile-photo");
photo.src = profile_info["profile_picture"];

document.getElementById('displayname').value = profile_info["displayname"];

const email = document.getElementById("email");
email.value = profile_info["email"];

document.getElementsByClassName("back-button")[0].addEventListener("click", async (e) => {
    e.preventDefault();
    router.handlePopState();
});


document.body.addEventListener('click', async function (event) {
  const target = event.target;
  const form = target.closest('form');

  if (!form) return;

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
      console.log(await result.json());
    }
    if (form.querySelector('input').id == "email") {
      const result = await api.patch("/profile/", {
        email: form.querySelector('input').value,
      });
      console.log(await result.json());
    }
    resetButtons(form, editBtn, confirmBtn, cancelBtn);
  } else if (target.closest('.cancel-button')) {
    resetButtons(form, editBtn, confirmBtn, cancelBtn);
  }
});

document.getElementById("delete").addEventListener('click', async function (event) {
  const result = await api.delete("/profile/");
  event.preventDefault();
});

function resetButtons(form, editBtn, confirmBtn, cancelBtn) {
  form.querySelector('input').disabled = true;
  form.querySelector('input').readOnly = true;
  form.classList.remove('editing');
  editBtn.style.display = 'inline-block';
  confirmBtn.style.display = 'none';
  cancelBtn.style.display = 'none';
}