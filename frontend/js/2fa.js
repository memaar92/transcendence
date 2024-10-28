import { api } from "./api.js";
import { router } from "./app.js";

document.getElementById("code-form-submit").addEventListener("click", async (e) => {
  e.preventDefault();

  const result = await api.post("/token/2fa/verify/", {
    code_2fa: document.getElementById("code").value
  });
  const user_info = await result.json();
  if (result && result.ok) {
      router.navigate("/main_menu");
  } else {
    showAlert(user_info["code_2fa"] ? user_info["code_2fa"] : user_info["detail"], "alert-danger");
  }
});

function showAlert(message, type) {
    const alertContainer = document.getElementById("alertContainer");
  
    const alertElement = document.createElement("div");
    alertElement.classList.add(
      "alert",
      type,
      "alert-dismissible",
      "fade",
      "show"
    );
    alertElement.setAttribute("role", "alert");
  
    alertElement.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
  
    alertContainer.appendChild(alertElement);
  
    // Initialize the Bootstrap alert
    new bootstrap.Alert(alertElement);
  }