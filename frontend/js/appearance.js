import { router } from "./app";

document.getElementById("back").addEventListener("click", async (e) => {
    router.navigate("/main_menu");
  });