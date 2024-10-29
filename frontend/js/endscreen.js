const screen_text = document.getElementById("endscreen-text");

if (localStorage.getItem("local")) {
    screen_text.innerHTML = "GOOD&nbspGAME"
    localStorage.removeItem("local");
}
else if (localStorage.getItem("win")) {
    screen_text.innerHTML = "YOU&nbspWIN"
} else {
    screen_text.innerHTML = "YOU&nbspLOSE"
}