// match.js

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
        const data = JSON.parse(e.data);
        console.log('Received match message:', data);
    }
}

function hideReconnectButton() {
    const reconnectButton = document.getElementById('reconnectButton');
    if (reconnectButton) {
        reconnectButton.style.display = 'none';
    }
}