import { api } from "./api.js";
import { hubSocket, router, showAlert } from "./app.js";

const r = await api.get("/profile/");

function start_game(match_id) {
  let is_local_match = false;
  let user_id_p1 = null;
  let user_id_p2 = null;

  let leftPlayerScore = 0;
  let rightPlayerScore = 0;

  const matchSocket = new WebSocket(
    "wss://" + window.location.host + "/wss/pong/match/" + match_id + "/"
  );
  matchSocket.onopen = function (e) {
    console.log("Match WebSocket connection established.");
    hideReconnectButton();
  };

  matchSocket.onclose = function (e) {
    console.error("Match WebSocket connection closed.");
  };

  matchSocket.onerror = function (e) {
    console.error("Match WebSocket error:", e);
    router.navigate("/main_menu");
  };

  matchSocket.binaryType = "arraybuffer"; // Set the binary type of the WebSocket to ArrayBuffer

  matchSocket.onmessage = function (e) {
    const data = e.data;

    if (typeof data === "string") {
      // Handle JSON data
      try {
        const jsonData = JSON.parse(data);
        // Process JSON data
        console.log("Received JSON data:", jsonData);

        if (jsonData.type === "start_timer_update") {
          timerValue = jsonData.start_timer;
          console.log("Received timer update:", timerValue);
        } else if (jsonData.type === "player_scores") {
          leftPlayerScore = jsonData.player1;
          rightPlayerScore = jsonData.player2;
          console.log(
            "Received player scores:",
            leftPlayerScore,
            rightPlayerScore
          );
        } else if (jsonData.type === "game_over") {
          matchSocket.close();
          document.removeEventListener("keydown", key_down, false);
          document.removeEventListener("keyup", key_up, false);
          localStorage.setItem("win", false);
          router.navigate("/endscreen");
        } else if (jsonData.type === "user_mapping") {
          is_local_match = jsonData.is_local_match;
          user_id_p1 = jsonData.player1;
          console.log("is_local_match:", is_local_match);
          console.log("user_id_p1:", user_id_p1);
          if (!is_local_match) {
            user_id_p2 = jsonData.player2;
            console.log("user_id_p2:", user_id_p2);
          }
        }
      } catch (error) {
        console.error("Failed to parse JSON data:", error);
      }
    } else if (data instanceof ArrayBuffer) {
      // Handle binary data
      const view = new DataView(data);

      // Read the six floats from the DataView
      // Assuming the data is little-endian; if not, set the second argument to false
      const player1PosX = view.getFloat32(0, true) * 100;
      const player1PosY = view.getFloat32(4, true) * 100;
      const player2PosX = view.getFloat32(8, true) * 100;
      const player2PosY = view.getFloat32(12, true) * 100;
      const ballPosX = view.getFloat32(16, true) * 100;
      const ballPosY = view.getFloat32(20, true) * 100;

      // Update the paddles and ball
      leftPaddle.x = player1PosX;
      leftPaddle.y = player1PosY;
      rightPaddle.x = player2PosX;
      rightPaddle.y = player2PosY;
      ball.x = ballPosX;
      ball.y = ballPosY;
    } else {
      console.error("Unsupported data type:", typeof data);
    }
  };

  function hideReconnectButton() {
    const reconnectButton = document.getElementById("reconnectButton");
    if (reconnectButton) {
      reconnectButton.style.display = "none";
    }
  }

  // Create a new canvas element
  const canvas = document.createElement("canvas");
  //   document.body.appendChild(canvas); // Append the canvas to the body or any other container

  //   // Initialize canvas and context
  const canvasWidth = canvas.width;
  const canvasHeight = canvas.height;

  let timerValue = null; // Initialize timer value
  let winner = null; // Initialize winner

  let move_up_player_1 = false;
  let move_down_player_1 = false;
  let move_up_player_2 = false;
  let move_down_player_2 = false;

  function sendPlayerInput(up, down, player_id) {
    let message = {};
    if (up && down) {
      message = create_player_input_message(0, player_id);
    } else if (up && !down) {
      message = create_player_input_message(-1, player_id);
    } else if (!up && down) {
      message = create_player_input_message(1, player_id);
    } else {
      message = create_player_input_message(0, player_id);
    }
    matchSocket.send(JSON.stringify(message));
  }

  function create_player_input_message(direction, player_id) {
    return { type: "player_input", direction: direction, player_id: player_id };
  }

  // Function to calculate the offset between the element and the filter
  function calculateOffset(element, filter) {
    const elementX = parseFloat(
      element.getAttribute("x") || element.getAttribute("cx")
    );
    const elementY = parseFloat(
      element.getAttribute("y") || element.getAttribute("cy")
    );
    const filterX = parseFloat(filter.getAttribute("x"));
    const filterY = parseFloat(filter.getAttribute("y"));

    return {
      offsetX: filterX - elementX,
      offsetY: filterY - elementY,
    };
  }

  // Generic function to move an element and update the filter coordinates
  function moveElement(elementId, filterId, newX, newY) {
    const element = document.getElementById(elementId);
    const filter = document.getElementById(filterId);

    if (element && filter) {
      // Calculate the offset between the element and the filter
      const { offsetX, offsetY } = calculateOffset(element, filter);

      if (elementId == "left-pad") {
        element.setAttribute("y", newY);
        // Update filter position
        const filterY = newY + offsetY;
        filter.setAttribute("y", filterY);
        return;
      } else if (element.tagName === "rect") {
        element.setAttribute("y", newY);
        element.setAttribute("x", newX);
      } else if (element.tagName === "circle") {
        element.setAttribute("cx", newX);
        element.setAttribute("cy", newY);
        // Calculate new filter position based on offset
      }
      const filterX = newX + offsetX;
      // Update filter position
      filter.setAttribute("x", filterX);
      const filterY = newY + offsetY;
      filter.setAttribute("y", filterY);
    }
  }

  // Paddle properties
  const paddleWidth = 0.5 * 100;
  const paddleHeight = 2 * 100;
  const ballSize = 0.2 * 100;
  const leftPaddle = {
    x: 0,
    y: canvasHeight / 2 - paddleHeight / 2,
  };
  const rightPaddle = {
    x: canvasWidth - paddleWidth,
    y: canvasHeight / 2 - paddleHeight / 2,
  };

  const ball = {
    size: ballSize,
    x: canvasWidth / 2 - ballSize / 2,
    y: canvasHeight / 2 - ballSize / 2,
  };

  function key_down(event) {
    let stateChangedPlayer1 = false;
    let stateChangedPlayer2 = false;
    switch (event.code) {
      case "KeyW": // 'W' key
        if (!move_up_player_1) {
          move_up_player_1 = true;
          stateChangedPlayer1 = true;
        }
        break;
      case "KeyS": // 'S' key
        if (!move_down_player_1) {
          move_down_player_1 = true;
          stateChangedPlayer1 = true;
        }
        break;
      case "KeyO": // 'O' key
        event.preventDefault(); // Prevent default behavior
        if (!move_up_player_2) {
          move_up_player_2 = true;
          stateChangedPlayer2 = true;
        }
        break;
      case "KeyL": // 'L' key
        event.preventDefault(); // Prevent default behavior
        if (!move_down_player_2) {
          move_down_player_2 = true;
          stateChangedPlayer2 = true;
        }
        break;
    }
    if (stateChangedPlayer1) {
      sendPlayerInput(move_up_player_1, move_down_player_1, 0);
    }
    if (stateChangedPlayer2) {
      sendPlayerInput(move_up_player_2, move_down_player_2, 1);
    }
  }
  function key_up(event) {
    let stateChangedPlayer1 = false;
    let stateChangedPlayer2 = false;
    switch (event.code) {
      case "KeyW":
        if (move_up_player_1) {
          move_up_player_1 = false;
          stateChangedPlayer1 = true;
        }
        break;
      case "KeyS":
        if (move_down_player_1) {
          move_down_player_1 = false;
          stateChangedPlayer1 = true;
        }
        break;
      case "KeyO":
        event.preventDefault(); // Prevent default behavior
        if (move_up_player_2) {
          move_up_player_2 = false;
          stateChangedPlayer2 = true;
        }
        break;
      case "KeyL":
        event.preventDefault(); // Prevent default behavior
        if (move_down_player_2) {
          move_down_player_2 = false;
          stateChangedPlayer2 = true;
        }
        break;
    }
    if (stateChangedPlayer1) {
      sendPlayerInput(move_up_player_1, move_down_player_1, 0);
    }
    if (stateChangedPlayer2) {
      sendPlayerInput(move_up_player_2, move_down_player_2, 1);
    }
  }
  document.addEventListener("keydown", key_down, false);
  document.addEventListener("keyup", key_up, false);

  const countdownElement = document.getElementById("countdown");

  function draw() {
    // Draw ball and paddles
    moveElement("ball", "ball-filter", ball.x, ball.y);
    moveElement("left-pad", "left-pad-filter", leftPaddle.x, leftPaddle.y);
    moveElement("right-pad", "right-pad-filter", rightPaddle.x, rightPaddle.y);

    try {
      document.getElementById("left-score").innerHTML = leftPlayerScore;
      document.getElementById("right-score").innerHTML = rightPlayerScore;
    } catch (error) {}

    //   drawPaddle(leftPaddle);
    //   drawPaddle(rightPaddle);
    //   drawBall();
    //   drawScores(); // Draw the scores

    if (timerValue !== null && timerValue > 0) {
      countdownElement.textContent = timerValue;
    } else if (timerValue == 0) {
      countdownElement.innerHTML = "";
    }
    //   if (winner !== null) {
    //       drawWinner(winner);
    //   }

    //   // Request next frame
    requestAnimationFrame(draw);
  }

  // Start animation
  draw();
}

function local_match_callback(message) {
  if (message.error_message) {
    showAlert(message.error_message);
    router.navigate("/main_menu")
  } else if (message.local_match_created) {
    console.log(message)
  }
}

hubSocket.registerCallback(local_match_callback)
hubSocket.send({type: "local_match_create"})
