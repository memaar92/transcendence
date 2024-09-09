import { api } from "./api.js";

document.getElementById("2fa").addEventListener("click", async (e) => {
  e.preventDefault();
  if (document.getElementById('qrPhoto'))
    return;
  const result = await api.get("/2fa/setup/");
  console.log("register call finished");
  console.log(result);
  const user_info = await result.json();
  console.log(user_info);
  const img = new Image();
  img.src = `data:image/png;base64,${user_info["qr_code"]}`;
  img.id = 'qrPhoto';
  document.getElementById("qrCode").appendChild(img);
});
