import { sendWebSocketMessage } from './webSocketHelper.js';
import { matchmakingSocket } from './matchmaking.js';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('tournament-form');
    const tournamentList = document.getElementById('tournament-list');

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

    matchmakingSocket.addEventListener('open', () => {
        // Fetch the current tournament list immediately after connecting
        TournamentRequests.getTournaments();
    });

    matchmakingSocket.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'tournaments') {
            updateTournamentList(data.tournaments);
        }
    });

    function updateTournamentList(tournaments) {
        tournamentList.innerHTML = ''; // Clear the list
        tournaments.forEach(tournament => {
            const row = document.createElement('div');
            row.className = 'tournament-row';
            row.innerHTML = `
                <div>ID: ${tournament.id}</div>
                <div>Name: ${tournament.name}</div>
                <div>Max Players: ${tournament.max_players}</div>
                <div>Owner: ${tournament.owner}</div>
                <div>Users: ${tournament.users.join(', ')}</div>
                <button class="register-button" data-id="${tournament.id}">Register</button>
                <button class="unregister-button" data-id="${tournament.id}">Unregister</button>
                <button class="start-button" data-id="${tournament.id}" ${tournament.is_owner ? '' : 'disabled'}>Start</button>
                <button class="cancel-button" data-id="${tournament.id}" ${tournament.is_owner ? '' : 'disabled'}>Cancel</button>
            `;
            tournamentList.appendChild(row);
        });

        // Add event listeners to the buttons
        document.querySelectorAll('.register-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const tournamentId = event.target.getAttribute('data-id');
                TournamentRequests.register(tournamentId);
            });
        });

        document.querySelectorAll('.unregister-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const tournamentId = event.target.getAttribute('data-id');
                TournamentRequests.unregister(tournamentId);
            });
        });

        document.querySelectorAll('.start-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const tournamentId = event.target.getAttribute('data-id');
                TournamentRequests.start(tournamentId);
            });
        });

        document.querySelectorAll('.cancel-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const tournamentId = event.target.getAttribute('data-id');
                TournamentRequests.unregister(tournamentId);
            });
        });
    }

    // Automatically update the list every 2 seconds
    setInterval(() => {
        TournamentRequests.getTournaments();
    }, 2000);
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

    static cancel(tournament_id) {
        this.sendRequest("cancel", { tournament_id });
    }

    static getTournaments() {
        this.sendRequest("get_open_tournaments", {});
    }
}