
//     let move_up = false;
//     let move_down = false;
//     matchSocket = connectWebSocket(url);

//     function sendPlayerState() {
//         let message = {};
//         if (move_up && move_down) {
//             message = { "type": "player_update", "payload": { direction: 0 } };
//         } else if (move_up && !move_down) {
//             message = { "type": "player_update", "payload": { direction: -1 } };
//         } else if (!move_up && move_down) {
//             message = { "type": "player_update", "payload": { direction: 1 } };
//         } else {
//             message = { "type": "player_update", "payload": { direction: 0 } };
//         }
//         matchSocket.send(JSON.stringify(message));
//     }

//     function sendSetup(socket) {
//         const message = { "type": "setup", "matchType": "onlineMM" };
//         // Check if the WebSocket connection is already open
//         if (socket.readyState === WebSocket.OPEN) {
//             socket.send(JSON.stringify(message));
//         } else {
//             // Wait for the connection to open
//             socket.addEventListener('open', function() {
//                 socket.send(JSON.stringify(message));
//             });
//         }
//     }
    
//     function connectWebSocket(url) {
//         const matchSocket = new WebSocket(url);
        
//         matchSocket.onopen = function(e) {
//             console.log('WebSocket connection established.');
//             retryCount = 0;
//         };
        
//         matchSocket.onclose = function(e) {
//             console.error('WebSocket connection closed.');
//         };
        
//         matchSocket.onerror = function(e) {
//             console.error('WebSocket error: ' + e);
//             if (retryCount < maxRetries) {
//                 setTimeout(() =>  {
//                     console.log(`Attempting to reconnect... (${retryCount + 1})`);
//                     connectWebsocket(url); // Try to reconnect
//                     retryCount++;
//                 }, retryDelay);
//             } else {
//                 console.error("Max retries reached. Unable to connect to WebSocket.");
//             }
//         };

//         return matchSocket;
//     }

//     // Paddle properties
//     const paddleWidth = 20;
//     const paddleHeight = 100;
//     const leftPaddle = {
//         x: 0,
//         y: 0
//     };
//     const rightPaddle = {
//         x: 0,
//         y: 0
//     };
    
//     const ball = {
//         x: 0,
//         y: 0,
//         radius: 10
//     };

//     matchSocket.binaryType = 'arraybuffer'; // Set the binary type of the WebSocket to ArrayBuffer

//     matchSocket.onmessage = function(e) {
//         const data = e.data;

//         if (typeof data === 'string') {
//             // Handle JSON data
//             try {
//                 const jsonData = JSON.parse(data);
//                 // Process JSON data
//                 console.log('Received JSON data:', jsonData);
//                 // Example: Update some match state based on JSON data
//                 // ...
//             } catch (error) {
//                 console.error('Failed to parse JSON data:', error);
//             }
//         } else if (data instanceof ArrayBuffer) {
//             // Handle binary data
//             const view = new DataView(data);

//             // Read the six floats from the DataView
//             // Assuming the data is little-endian; if not, set the second argument to false
//             const player1PosX = view.getFloat32(0, true);
//             const player1PosY = view.getFloat32(4, true);
//             const player2PosX = view.getFloat32(8, true);
//             const player2PosY = view.getFloat32(12, true);
//             const ballPosX = view.getFloat32(16, true);
//             const ballPosY = view.getFloat32(20, true);

//             // Update the paddles and ball
//             leftPaddle.x = player1PosX;
//             leftPaddle.y = player1PosY;
//             rightPaddle.x = player2PosX;
//             rightPaddle.y = player2PosY;
//             ball.x = ballPosX;
//             ball.y = ballPosY;
//         } else {
//             console.error('Unsupported data type:', typeof data);
//         }
//     };

// // Event listeners for key down
// document.addEventListener('keydown', (event) => {
//     let stateChanged = false;
//     switch(event.code) {
//         case 'ArrowUp':
//             if (!move_up) {
//                 move_up = true;
//                 stateChanged = true;
//             }
//             break;
//         case 'ArrowDown':
//             if (!move_down) {
//                 move_down = true;
//                 stateChanged = true;
//             }
//             break;
//         case 'KeyW': // 'W' key
//             if (!move_up) {
//                 move_up = true;
//                 stateChanged = true;
//             }
//             break;
//         case 'KeyS': // 'S' key
//             if (!move_down) {
//                 move_down = true;
//                 stateChanged = true;
//             }
//             break;
//     }
//     if (stateChanged) {
//         sendPlayerState();
//     }
// });

// // Event listeners for key up
// document.addEventListener('keyup', (event) => {
//     let stateChanged = false;
//     switch(event.code) {
//         case 'ArrowUp':
//             if (move_up) {
//                 move_up = false;
//                 stateChanged = true;
//             }
//             break;
//         case 'ArrowDown':
//             if (move_down) {
//                 move_down = false;
//                 stateChanged = true;
//             }
//             break;
//         case 'KeyW':
//             if (move_up) {
//                 move_up = false;
//                 stateChanged = true;
//             }
//             break;
//         case 'KeyS':
//             if (move_down) {
//                 move_down = false;
//                 stateChanged = true;
//             }
//             break;
//     }
//     if (stateChanged) {
//         sendPlayerState();
//     }
// });
    
    
            
            // // Initialize canvas and context
            // const canvas = document.getElementById('gameCanvas');
            // const ctx = canvas.getContext('2d');
            
            // // Ball properties
            
            // function drawBall() {
            //     ctx.beginPath();
            //     ctx.fillStyle = '#FFFFFF';
            //     ctx.fillRect(ball.x, ball.y, ball.radius * 2, ball.radius * 2);
            //     // ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI*2);
            //     ctx.fill();
            //     ctx.closePath();
            // }
    
            // function drawPaddle(paddle) {
            //     ctx.beginPath();
            //     ctx.fillStyle = '#0095DD';
            //     ctx.fillRect(paddle.x, paddle.y, paddleWidth, paddleHeight);
            //     ctx.fill();
            //     ctx.closePath();
            // }
    
            // function draw() {
            //     // Clear canvas
            //     ctx.clearRect(0, 0, canvas.width, canvas.height);
    
            //     // Draw ball and paddles
            //     drawPaddle(leftPaddle);
            //     drawPaddle(rightPaddle);
            //     drawBall();
                
            //     // Request next frame
            //     requestAnimationFrame(draw);
            // }
    
            // sendSetup(matchSocket);
            // // Start animation
            // draw();
