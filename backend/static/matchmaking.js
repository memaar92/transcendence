import { sendWebSocketMessage } from "./webSocketHelper";

let retryCount = 0;
const maxRetries = 5;
const retryDelay = 2000; // Milliseconds
let match_id = null;
let isActiveTab = false;

const matchmakingSocket = new WebSocket('ws://' + window.location.host + '/ws/pong/matchmaking/');

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

// Socket event handlers

matchmakingSocket.onopen = function(e) {
    console.log('Matchmaking WebSocket connection established.');
};

matchmakingSocket.onclose = function(e) {
    console.error('Matchmaking WebSocket connection closed.');
};

matchmakingSocket.onerror = function(e) {
    console.error('Matchmaking WebSocket error:', e);
};

matchmakingSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log('Received matchmaking message:', data);
    if (data.type === "match_assigned") {
        if (data.match_id) {
            console.log('Match found! Match ID: ' + data.match_id);
            match_id = data.match_id;
            connectToMatch(match_id);
        }
    } else if (data.type === "match_in_progress") {
        console.log('Match in progress.');
        showReconnectButton(data.match_id); // Pass the correct match_id
    } else if (data.type === "registered") {
        console.log('Registered to match.');
        connectToMatch(match_id);
    } else if (data.type === "registration_timeout") {
        console.log('Registration timeout.');
    } else if (data.type === "registration_error") {
        console.error('Registration error:', data.error);
    }
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

class MatchmakingRequests {
    static sendRequest(requestType, data) {
        console.log(`${requestType} request with data:`, data);
        sendWebSocketMessage(matchmakingSocket, {
            "type": "matchmaking",
            "request": requestType,
            ...data,
        });
    }

    static joinOnlineMatchmakingQueue() {
        this.sendRequest("match", { match_type: "online" });
    }

    static createLocalMatch() {
        this.sendRequest("match", { match_type: "local" });
    }
}

class TournamentRequests {
    static sendRequest(requestType, data) {
        console.log(`${requestType} request with data:`, data);
        sendWebSocketMessage(matchmakingSocket, {
            "type": "tournament",
            "request": requestType,
            ...data,
        });
    }

    static create(name, max_players) {
        this.sendRequest("create", { name, max_players });
    }

    static register(tournament_id) {
        this.sendRequest("register", { tournament_id });
    }

    static unregister(tournament_id) {
        this.sendRequest("unregister", { tournament_id });
    }

    static start(tournament_id) {
        this.sendRequest("start", { tournament_id });
    }

    static getTournaments() {
        this.sendRequest("get_open_tournaments", {});
    }
}

document.getElementById('join-queue-button').onclick = MatchmakingRequests.joinOnlineMatchmakingQueue;