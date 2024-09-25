import { sendWebSocketMessage } from "./webSocketHelper.js";

let retryCount = 0;
const maxRetries = 5;
const retryDelay = 2000; // Milliseconds
let match_id = null;
let isActiveTab = false;
let matchmakingSocket = null;

function createWebSocket() {
    matchmakingSocket = new WebSocket('ws://' + window.location.host + '/ws/pong/matchmaking/');

    // Socket event handlers
    matchmakingSocket.onopen = function(e) {
        console.log('Matchmaking WebSocket connection established.');
        retryCount = 0; // Reset retry count on successful connection
    };

    matchmakingSocket.onclose = function(e) {
        console.error('Matchmaking WebSocket connection closed.');
        attemptReconnect();
    };

    matchmakingSocket.onerror = function(e) {
        console.error('Matchmaking WebSocket error:', e);
        matchmakingSocket.close(); // Close the socket to trigger onclose event
    };

    matchmakingSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('Received matchmaking message:', data);
        if (data.type === "match_ready") {
            if (data.match_id) {
                console.log('Match found! Match ID: ' + data.match_id);
                match_id = data.match_id;
                connectToMatch(match_id);
            }
        } else if (data.type === "match_in_progress") {
            console.log('Match in progress.');
            showReconnectButton(data.match_id); // Pass the correct match_id
        } else if (data.state === "already_in_game") {
            console.log('User is already in a game.');
        } else if (data.state === "registered") {
            console.log('User registered for match.');
            showCancelButton();
        } else if (data.state === "registration_error") {
            console.log('Error registering user.');
        } else if (data.state === "registration_timeout") {
            console.log('Registration timeout.');
        }
    };
}

function attemptReconnect() {
    if (retryCount < maxRetries) {
        retryCount++;
        console.log(`Attempting to reconnect... (${retryCount}/${maxRetries})`);
        setTimeout(createWebSocket, retryDelay);
    } else {
        console.error('Max retries reached. Could not reconnect to WebSocket.');
    }
}

// Monitor which tab is active
document.addEventListener("visibilitychange", function() {
    if (document.visibilityState === "visible") {
        isActiveTab = true;
        notifyTabActive();
    } else {
        isActiveTab = false;
    }
});

// Notify the server when the tab is active
function notifyTabActive() {
    sendWebSocketMessage(matchmakingSocket, {
        type: "tab_active",
        active: isActiveTab,
    });
}

function showReconnectButton(match_id) {
    const reconnectButton = document.getElementById('reconnectButton');
    if (reconnectButton) {
        reconnectButton.style.display = 'block';
        reconnectButton.onclick = function() {
            connectToMatch(match_id);
        };
    }
}

function hideReconnectButton() {
    const reconnectButton = document.getElementById('reconnectButton');
    if (reconnectButton) {
        reconnectButton.style.display = 'none';
    }
}

function showCancelButton() {
    const cancelButton = document.getElementById('cancel-queue-button');
    if (cancelButton) {
        cancelButton.style.display = 'block';
        cancelButton.onclick = MatchmakingRequests.cancelQueue;
    }
}

function hideCancelButton() {
    const cancelButton = document.getElementById('cancel-queue-button');
    if (cancelButton) {
        cancelButton.style.display = 'none';
    }
}

class MatchmakingRequests {
    static sendRequest = (requestType, data) => {
        console.log(`${requestType} request with data:`, data);
        sendWebSocketMessage(matchmakingSocket, {
            "type": "matchmaking",
            "request": requestType,
            ...data,
        });
    }

    static joinOnlineMatchmakingQueue = () => {
        this.sendRequest("register", { match_type: "online" });
        showCancelButton();
    }

    static createLocalMatch = () => {
        this.sendRequest("register", { match_type: "local" });
    }

    static cancelQueue = () => {
        this.sendRequest("unregister", {});
        hideCancelButton();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const joinQueueButton = document.getElementById('join-queue-button');
    if (joinQueueButton) {
        joinQueueButton.onclick = MatchmakingRequests.joinOnlineMatchmakingQueue;
    }
    createWebSocket(); // Initialize WebSocket connection when the document is loaded
});

// Export matchmakingSocket to make it accessible from other modules
export { matchmakingSocket };