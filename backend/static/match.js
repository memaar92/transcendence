window.connectToMatch = function(match_id) {
    const matchSocket = new WebSocket('ws://' + window.location.host + '/ws/pong/match/' + match_id + '/');
    matchSocket.onopen = function(e) {
        console.log('Match WebSocket connection established.');
        const canvas = document.getElementById('gameCanvas');
        canvas.style.display = 'block'; // Show the canvas
        hideReconnectButton();
    };

    matchSocket.onclose = function(e) {
        console.error('Match WebSocket connection closed.');
    };

    matchSocket.onerror = function(e) {
        console.error('Match WebSocket error:', e);
    };

    matchSocket.onmessage = function(e) {
        // const data = JSON.parse(e.data);
        // console.log('Received match message:', data);
    };

    function hideReconnectButton() {
        const reconnectButton = document.getElementById('reconnectButton');
        if (reconnectButton) {
            reconnectButton.style.display = 'none';
        }
    }

    let move_up_player_1 = false;
    let move_down_player_1 = false;
    let move_up_player_2 = false;
    let move_down_player_2 = false;

    function sendPlayerStateP1() {
        let message = {};
        if (move_up_player_1 && move_down_player_1) {
            message = { "type": "player_update", "payload": { direction: 0, player_key_id: 0 } };
        } else if (move_up_player_1 && !move_down_player_1) {
            message = { "type": "player_update", "payload": { direction: -1, player_key_id: 0 } };
        } else if (!move_up_player_1 && move_down_player_1) {
            message = { "type": "player_update", "payload": { direction: 1, player_key_id: 0 } };
        } else {
            message = { "type": "player_update", "payload": { direction: 0, player_key_id: 0 } };
        }
        matchSocket.send(JSON.stringify(message));
    }

    function sendPlayerStateP2() {
        let message = {};
        if (move_up_player_2 && move_down_player_2) {
            message = { "type": "player_update", "payload": { direction: 0, player_key_id: 1 } };
        } else if (move_up_player_2 && !move_down_player_2) {
            message = { "type": "player_update", "payload": { direction: -1, player_key_id: 1 } };
        } else if (!move_up_player_2 && move_down_player_2) {
            message = { "type": "player_update", "payload": { direction: 1, player_key_id: 1 } };
        } else {
            message = { "type": "player_update", "payload": { direction: 0, player_key_id: 1 } };
        }
        matchSocket.send(JSON.stringify(message));
    }

    // Paddle properties
    const paddleWidth = 0.5 * 100;
    const paddleHeight = 2 * 100;
    const leftPaddle = {
        x: 0,
        y: 0
    };
    const rightPaddle = {
        x: 0,
        y: 0
    };
    
    const ball = {
        x: 0,
        y: 0,
        radius: 0.2 * 100
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
                if (jsonData.type === 'game_update') {
                    console.log('Received game update:', jsonData.payload);
                    const player1PosX = jsonData.data.paddle_left.x * 100;
                    const player1PosY = jsonData.data.paddle_left.y * 100;
                    const player2PosX = jsonData.data.paddle_right.x * 100;
                    const player2PosY = jsonData.data.paddle_right.y * 100;
                    const ballPosX = jsonData.data.ball.x * 100;
                    const ballPosY = jsonData.data.ball.y * 100;

                    leftPaddle.x = player1PosX;
                    leftPaddle.y = player1PosY;
                    rightPaddle.x = player2PosX;
                    rightPaddle.y = player2PosY;
                    ball.x = ballPosX;
                    ball.y = ballPosY;
                }
            } catch (error) {
                console.error('Failed to parse JSON data:', error);
            }
        } else if (data instanceof ArrayBuffer) {
            // Handle binary data
            const view = new DataView(data);

            // Read the six floats from the DataView
            // Assuming the data is little-endian; if not, set the second argument to false
            const player1PosX = view.getFloat32(0, true);
            const player1PosY = view.getFloat32(4, true);
            const player2PosX = view.getFloat32(8, true);
            const player2PosY = view.getFloat32(12, true);
            const ballPosX = view.getFloat32(16, true);
            const ballPosY = view.getFloat32(20, true);

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
            case 'ArrowUp':
                if (!move_up_player_2) {
                    move_up_player_2 = true;
                    stateChangedPlayer2 = true;
                }
                break;
            case 'ArrowDown':
                if (!move_down_player_2) {
                    move_down_player_2 = true;
                    stateChangedPlayer2 = true;
                }
                break;
        }
        if (stateChangedPlayer1) {
            sendPlayerStateP1();
        }
        if (stateChangedPlayer2) {
            sendPlayerStateP2();
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
            case 'ArrowUp':
                if (move_up_player_2) {
                    move_up_player_2 = false;
                    stateChangedPlayer2 = true;
                }
                break;
            case 'ArrowDown':
                if (move_down_player_2) {
                    move_down_player_2 = false;
                    stateChangedPlayer2 = true;
                }
                break;
        }
        if (stateChangedPlayer1) {
            sendPlayerStateP1();
        }
        if (stateChangedPlayer2) {
            sendPlayerStateP2();
        }
    });

    // Initialize canvas and context
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;

    // Ball properties
    function drawBall() {
        ctx.beginPath();
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(
            Math.round(ball.x), 
            Math.round(ball.y), 
            Math.round(ball.radius * 2), 
            Math.round(ball.radius * 2)
        );
        // ctx.arc(Math.round(ball.x), Math.round(ball.y), Math.round(ball.radius), 0, Math.PI * 2);
        ctx.fill();
        ctx.closePath();
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

    function draw() {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw ball and paddles
        drawPaddle(leftPaddle);
        drawPaddle(rightPaddle);
        drawBall();
        
        // Request next frame
        requestAnimationFrame(draw);
    }

    // Start animation
    draw();
}