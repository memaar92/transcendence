import { api } from "./api.js";
import { hubSocket, router } from "./app.js";
import { showAlert } from "./app.js";
import  ChatHandler  from "./chatHandler.js";

await update_userinfo()

document.getElementById("back").addEventListener("click", async (e) => {
  router.navigate("/main_menu");
});

document.getElementById("upload-photo").addEventListener("change", async (e) => {
  let photo = document.getElementById("upload-photo").files[0];
  let formData = new FormData();
      
  formData.append("profile_picture", photo);
  await api.patch_multipart("/profile/", formData);

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
    if (form.querySelector('input').id == "email") {
      const result = await api.patch("/profile/", {
        email: form.querySelector('input').value,
      });
      if (result.status == 400)
        {
          await result.json()
            .then(data => {
              if (data.errors) {
                showAlert(data.errors.email);
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
    if (form.querySelector('input').id == "password") {
      const result = await api.patch("/profile/", {
        password: form.querySelector('input').value,
      });
      if (result.status == 400)
        {
          await result.json()
            .then(data => {
              if (data.errors) {
                showAlert(data.errors);
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

document.getElementById("logout").addEventListener('click', async function (event) {
  event.preventDefault();
  hubSocket.close();
  const chatHandler = ChatHandler.getInstance();
  await chatHandler.logout();
  await api.post("/token/logout/")
  await router.navigate("/");
});


document.getElementById("deleteModal").addEventListener('click', async function (event) {
    const modalContainer = document.createElement('div');
    modalContainer.className = 'modal fade';

    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Account deletion</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p>Really want to delete your account?</p>
            </div>
            <div class="modal-footer" style="padding-right: 3rem;">
                <button type="button" class="secondaryButton" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="dangerous-button" id="confirmDeletion">Delete</button>
            </div>
        </div>
      </div>
    `;

    // Append the modal container to the body
    document.body.prepend(modalContainer);

    let modalInstance;
    try {
      modalInstance = new bootstrap.Modal(modalContainer, {
        keyboard: true,
        backdrop: 'static'
      });
      modalInstance.show();
    } catch (error) {
      console.error('Error initializing modal:', error);
      modalContainer.remove();
      return;
    }

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        modalInstance.hide();
      }
    };

    document.addEventListener('keydown', handleEscapeKey);

    // Clean up event listeners and modal instance when the modal is hidden
    modalContainer.addEventListener('hidden.bs.modal', () => {
      modalContainer.remove();
      modalInstance.dispose();
      document.removeEventListener('keydown', handleEscapeKey);
    });
});


document.addEventListener('click', async function (event) {
  if (event.target && event.target.id === 'confirmDeletion') {
    const modalContainer = document.querySelector('.modal.fade');
    if (modalContainer) {
        const modalInstance = bootstrap.Modal.getInstance(modalContainer);
        if (modalInstance) {
            modalInstance.hide();
            modalContainer.remove();
        }
    }
    const result = await api.delete("/profile/");
    router.navigate("/home");
    event.preventDefault();
  }
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

  const photo = document.getElementById("profile-photo");
  photo.src = profile_info["profile_picture"];

  document.getElementById('displayname').value = profile_info["displayname"];

  const email = document.getElementById("email");
  email.value = profile_info["email"];

  const is42user = profile_info["is_42_auth"];
  const editEmail = document.getElementById("edit-email");
  const editPwd = document.getElementById("edit-pwd");
  if (is42user) {
    disableElement(editEmail);
    disableElement(editPwd);
  }

function disableElement(element) {
    element.disabled = true;
    element.style.backgroundColor = "#d3d3d3";
    element.style.cursor = "not-allowed";
    element.style.boxShadow = "0 4px 0 0 #a9a9a9";
}

}
