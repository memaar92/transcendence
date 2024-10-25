import { api } from "./api.js";
import { router } from "./app.js";

function getCodeInputValues() {
  const inputs = document.querySelectorAll(".code-input");
  let result = 0;

  inputs.forEach((input) => {
    const intValue = parseInt(input.value, 10);
    if (!isNaN(intValue)) {
      result += intValue;
      result *= 10;
    }
  });
  result /= 10;
  return result;
}

await api.post("/email/otp/", { id: localStorage.getItem("uid") });
document.getElementById("user-mail").innerText = localStorage.getItem("email");

document.getElementById("verify-email").addEventListener("click", async (e) => {
  e.preventDefault();
  const result = await api.post("/email/validate/", {
    id: localStorage.getItem("uid"),
    otp: getCodeInputValues(),
  });
  if (result.ok) {
    router.navigate("/main_menu");
  } else {
    document.getElementById("codeForm").classList.add("is-invalid");
  }
});

document.getElementById("resend").addEventListener("click", async (e) => {
  e.preventDefault();
  const result = await api.post("/email/otp/", {
    id: localStorage.getItem("uid"),
  });
  if (!result.ok) {
    document.getElementById("tooManyRequests").classList.remove("d-none");
    const errorResponse = await result.json();
    document.getElementById("errorText").textContent = await errorResponse[
      "detail"
    ];
    document.getElementById("resend").classList.add("is-invalid");
  }
});

document.querySelectorAll(".code-input").forEach((input, index, inputs) => {
  input.addEventListener("input", () => {
    if (input.value.length === 1 && index < inputs.length - 1) {
      inputs[index + 1].focus();
    }
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Backspace" && input.value.length === 0 && index > 0) {
      inputs[index - 1].focus();
    }
  });
});
