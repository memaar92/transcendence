/**
 * Sends a message to the WebSocket server.
 */
export function sendWebSocketMessage(socket, message) {
    console.log('Sending message:', message);
    socket.send(JSON.stringify(message));
}