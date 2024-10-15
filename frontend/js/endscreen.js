const screen_text = document.getElementById("endscreen-text");

if (localStorage.getItem("win")) {
    screen_text.innerHTML = "YOU&nbspWIN"
} else {
    screen_text.innerHTML = "YOU&nbspLOOSE"
}