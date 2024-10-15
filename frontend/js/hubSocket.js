import { router } from "./app.js"

class HubSocket {
    constructor() {
        console.log("Hub: constructor called");
        // this.retryCount = 0;
        // this.maxRetries = 5;
        // this.retryDelay = 2000;
        // this.match_id = null;
        // this.isActiveTab = false;
        this.lobbySocket = null;
        this.socket = null;
        this.callbackFunction = null;
    }

    connect() {
        if (this.socket)
            return;
        console.log("Hub: connecting");
        this.socket = new WebSocket('wss://' + window.location.host + '/wss/pong/matchmaking/');
        this.socket.onmessage = this.#handleMessage.bind(this);
    }

    close () {
        this.socket.close();
        this.socket = null;
    }

    send(message) {
        this.socket.send(JSON.stringify(message));
    }

    registerCallback(func) {
        console.log("Hub: registering callback");
        console.log("Hub: function", func);
        this.callbackFunction = func;
    }

    #handleMessage(e) {
        const data = JSON.parse(e.data);
        console.log("HUB: ", data)

        if (data.type == "tournament_finished"){
            localStorage.setItem("tournament_result", JSON.stringify(data.user_scores));
            localStorage.setItem("tournament_name", data.tournament_name);
            router.navigate("/tournament_review");
            return;
        }
        if (data.type == "remote_match_ready") {
            window.localStorage.setItem("game_id", data.match_id);
            router.navigate("/game");
        }

        if (this.callbackFunction)
        {
            this.callbackFunction(data);
        }

        // if (data.type === "remote_match_ready") {
        //     if (data.match_id) {
        //         console.log('Match found! Match ID: ' + data.match_id);
        //         match_id = data.match_id;
        //         connectToMatch(match_id);
        //     } else {
        //         console.error('Match ID not found.');
        //     }
        // } else if (data.type === "tournament_starting") {
        //     console.log('Tournament starting.');
        //     showOverlay('Tournament Starting', 'A tournament is starting.');
        // } else if (data.type === "match_in_progress") {
        //     console.log('Match in progress.');
        //     showReconnectButton(data.match_id); // Pass the correct match_id
        // } else if (data.type === "tournament_canceled") {
        //     console.log('Tournament canceled.');
        //     showOverlay('Tournament Canceled', 'A tournament has been canceled.');
        // } else if (data.state === "already_in_game") {
        //     console.log('User is already in a game.');
        // } else if (data.state === "registered") {
        //     console.log('User registered for match.');
        //     showCancelButton();
        // } else if (data.state === "registration_error") {
        //     console.log('Error registering user.');
        // } else if (data.state === "registration_timeout") {
        //     console.log('Registration timeout.');
        // }
    }
}

// Export matchmakingSocket to make it accessible from other modules
export default HubSocket