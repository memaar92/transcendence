import { sendWebSocketMessage } from './webSocketHelper.js';
import { matchmakingSocket } from './matchmaking.js';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('tournament-form');

    form.addEventListener('submit', (event) => {
        event.preventDefault();

        const name = document.getElementById('tournament-name').value;
        const maxPlayers = parseInt(document.getElementById('max-players').value, 10);
        console.log('Creating tournament:', name, maxPlayers);

        if (maxPlayers > 12) {
            alert('Max players cannot exceed 12.');
            return;
        }

        TournamentRequests.create(name, maxPlayers);
    });
});

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
        console.log('Tournament created.');
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