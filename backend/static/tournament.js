import { sendWebSocketMessage } from './webSocketHelper.js';
import { matchmakingSocket } from './matchmaking.js';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('tournament-form');
    const tournamentList = document.getElementById('tournament-list');

    form.addEventListener('submit', (event) => {
        event.preventDefault(); // Prevent the form from submitting

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
            const userCount = tournament.users.length; // Number of users registered in the tournament
            const isOwner = tournament.is_owner; // Is the current user the owner of the tournament
            const canStart = isOwner && userCount >= 2; // At least 2 players required to start

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
                <button class="start-button" data-id="${tournament.id}" ${canStart ? '' : 'disabled'}>Start</button>
                <button class="cancel-button" data-id="${tournament.id}" ${isOwner ? '' : 'disabled'}>Cancel</button>
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
                TournamentRequests.cancel(tournamentId);
            });
        });
    }

    // Automatically update the list every 0.5 seconds if the socket is still connected
    setInterval(() => {
        if (matchmakingSocket.readyState === WebSocket.OPEN) {
            TournamentRequests.getTournaments();
        }
    }, 2000);
});

class TournamentRequests {
    static create(name, max_players) {
        sendWebSocketMessage(matchmakingSocket, {
            type: "tournament_create",
            name: name,
            max_players: max_players,
        });
        console.log('Tournament create request sent');
    }

    static register(tournament_id) {
        sendWebSocketMessage(matchmakingSocket, {
            type: "tournament_register",
            tournament_id: tournament_id,
        });
    }

    static unregister(tournament_id) {
        sendWebSocketMessage(matchmakingSocket, {
            type: "tournament_unregister",
            tournament_id: tournament_id,
        });
    }

    static start(tournament_id) {
        sendWebSocketMessage(matchmakingSocket, {
            type: "tournament_start",
            tournament_id: tournament_id,
        });
    }

    static cancel(tournament_id) {
        sendWebSocketMessage(matchmakingSocket, {
            type: "tournament_cancel",
            tournament_id: tournament_id,
        });
    }

    static getTournaments() {
        sendWebSocketMessage(matchmakingSocket, {
            type: "tournament_get_open",
        });
    }
}