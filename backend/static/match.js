window.connectToMatch = function(match_id) {

    let is_local_match = false;
    let user_id_p1 = null;
    let user_id_p2 = null;

    let leftPlayerScore = 0;
    let rightPlayerScore = 0;

    const matchSocket = new WebSocket('wss://' + window.location.host + '/wss/pong/match/' + match_id + '/');
    matchSocket.onopen = function(e) {
        console.log('Match WebSocket connection established.');
        hideReconnectButton();
    };

    matchSocket.onclose = function(e) {
        console.error('Match WebSocket connection closed.');
    };

    matchSocket.onerror = function(e) {
        console.error('Match WebSocket error:', e);
    };

    matchSocket.binaryType = 'arraybuffer'; // Set the binary type of the WebSocket to ArrayBuffer

    matchSocket.onmessage = function(e) {
        const data = e.data;

        if (typeof data === 'string') {
            // Handle JSON data
            try {
                const jsonData = JSON.parse(data);
                // Process JSON data
                console.log('Received JSON data:', jsonData);
                
                if (jsonData.type === 'start_timer_update') {
                    timerValue = jsonData.start_timer;
                    console.log('Received timer update:', timerValue);
                } else if (jsonData.type === 'player_scores') {
                    leftPlayerScore = jsonData.player1;
                    rightPlayerScore = jsonData.player2;
                    console.log('Received player scores:', leftPlayerScore, rightPlayerScore);
                } else if (jsonData.type === 'game_over') {
                    winner = jsonData.data;
                    timerValue = null;
                    console.log('Game over:', winner);
                } else if (jsonData.type === 'user_mapping') {
                    is_local_match = jsonData.is_local_match;
                    user_id_p1 = jsonData.player1;
                    console.log('is_local_match:', is_local_match);
                    console.log('user_id_p1:', user_id_p1);
                    if (!is_local_match) {
                        user_id_p2 = jsonData.player2;
                        console.log('user_id_p2:', user_id_p2);
                    }
                }
            } catch (error) {
                console.error('Failed to parse JSON data:', error);
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
            console.error('Unsupported data type:', typeof data);
        }
    };

    function hideReconnectButton() {
        const reconnectButton = document.getElementById('reconnectButton');
        if (reconnectButton) {
            reconnectButton.style.display = 'none';
        }
    }

    // Create a new canvas element
    const canvas = document.createElement('canvas');
    canvas.id = 'gameCanvas';
    canvas.width = 1600; // Set the desired width
    canvas.height = 900; // Set the desired height
    canvas.style.backgroundColor = '#000000'; // Set the background color
    document.body.appendChild(canvas); // Append the canvas to the body or any other container

    // Initialize canvas and context
    const ctx = canvas.getContext('2d');
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
        return { "type": "player_input", "direction": direction, "player_id": player_id };
    }

    // Paddle properties
    const paddleWidth = 0.5 * 100;
    const paddleHeight = 2 * 100;
    const ballSize = 0.2 * 100;
    const leftPaddle = {
        x: 0,
        y: canvasHeight / 2 - paddleHeight / 2
    };
    const rightPaddle = {
        x: canvasWidth - paddleWidth,
        y: canvasHeight / 2 - paddleHeight / 2
    };
    
    const ball = {
        size: ballSize,
        x: canvasWidth / 2 - ballSize / 2,
        y: canvasHeight / 2 - ballSize / 2
    };

    // Event listeners for key down
    document.addEventListener('keydown', (event) => {
        let stateChangedPlayer1 = false;
        let stateChangedPlayer2 = false;
        switch(event.code) {
            case 'KeyW': // 'W' key
                if (!move_up_player_1) {
                    move_up_player_1 = true;
                    stateChangedPlayer1 = true;
                }
                break;
            case 'KeyS': // 'S' key
                if (!move_down_player_1) {
                    move_down_player_1 = true;
                    stateChangedPlayer1 = true;
                }
                break;
            case 'KeyO': // 'O' key
                event.preventDefault(); // Prevent default behavior
                if (!move_up_player_2) {
                    move_up_player_2 = true;
                    stateChangedPlayer2 = true;
                }
                break;
            case 'KeyL': // 'L' key
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
    });

    // Event listeners for key up
    document.addEventListener('keyup', (event) => {
        let stateChangedPlayer1 = false;
        let stateChangedPlayer2 = false;
        switch(event.code) {
            case 'KeyW':
                if (move_up_player_1) {
                    move_up_player_1 = false;
                    stateChangedPlayer1 = true;
                }
                break;
            case 'KeyS':
                if (move_down_player_1) {
                    move_down_player_1 = false;
                    stateChangedPlayer1 = true;
                }
                break;
            case 'KeyO':
                event.preventDefault(); // Prevent default behavior
                if (move_up_player_2) {
                    move_up_player_2 = false;
                    stateChangedPlayer2 = true;
                }
                break;
            case 'KeyL':
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
    });

    // Ball properties
    function drawBall() {
        ctx.beginPath();
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(
            Math.round(ball.x), 
            Math.round(ball.y), 
            Math.round(ball.size),
            Math.round(ball.size)
        );
        // ctx.arc(Math.round(ball.x), Math.round(ball.y), Math.round(ball.radius), 0, Math.PI * 2);
        ctx.fill();
        ctx.closePath();
    }

    function drawScores() {
        ctx.font = 'bold 48px Arial';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
    
        // Draw left player score
        ctx.fillText(leftPlayerScore, canvasWidth / 4, 50);
    
        // Draw right player score
        ctx.fillText(rightPlayerScore, (canvasWidth / 4) * 3, 50);
    }

    function drawPaddle(paddle) {
        ctx.beginPath();
        ctx.fillStyle = '#0095DD';
        ctx.fillRect(
            Math.round(paddle.x), 
            Math.round(paddle.y), 
            Math.round(paddleWidth), 
            Math.round(paddleHeight)
        );
        ctx.fill();
        ctx.closePath();
    }

    // Function to draw the timer
    function drawTimer() {
        if (timerValue !== null) {
            ctx.font = 'bold 96px Arial';
            ctx.fillStyle = 'white';
            ctx.textAlign = 'center';
            ctx.fillText(timerValue, canvasWidth / 2, canvasHeight / 2);
        }
    }

    function drawWinner(winner) {
        ctx.font = 'bold 48px Arial';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.fillText('Winner: ' + winner + ' (This is the player ID, not the user ID)', canvasWidth / 2, canvasHeight / 2);
    }

    function draw() {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    
        // Draw ball and paddles
        drawPaddle(leftPaddle);
        drawPaddle(rightPaddle);
        drawBall();
        drawScores(); // Draw the scores
    
        if (timerValue !== null && timerValue > 0) {
            drawTimer();
        }
        if (winner !== null) {
            drawWinner(winner);
        }
        
        // Request next frame
        requestAnimationFrame(draw);
    }

    // Start animation
    draw();
}