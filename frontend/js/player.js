import { api } from "./api.js";
import { router } from "./app.js";
import { showAlert } from "./app.js"

await update_userinfo()

document.getElementById("upload-photo").addEventListener("change", async (e) => {
    let photo = document.getElementById("upload-photo").files[0];
    let formData = new FormData();
        
    formData.append("profile_picture", photo);
    await api.patch_multipart("/profile/", formData);
    
    await update_userinfo();
});

document.getElementById("player-content").addEventListener('click', async function (event) {
    const target = event.target;
    const form = target.closest('form');
    
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
                showAlert(data.errors.displayname);
              } else {
                showAlert('No errors found');
              }
            })
            .catch(error => {
              showAlert(`Error parsing JSON: ${error.message}`);
            });
  
        }
      }
      resetButtons(form, editBtn, confirmBtn, cancelBtn);
    } else if (target.closest('.cancel-button')) {
      resetButtons(form, editBtn, confirmBtn, cancelBtn);
    }
    await update_userinfo()
});

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
  
    const photo = document.getElementById("player-creation-photo");
    if (photo != null)
        photo.src = profile_info["profile_picture"];
    document.getElementById('displayname').value = profile_info["displayname"] || "";
}

document.getElementById("main_menu").addEventListener("click", async (e) => {
    e.preventDefault();
    await router.navigate("/main_menu");
});
