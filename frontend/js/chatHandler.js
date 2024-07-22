
async function obtainAuthToken(email, password) {
    try {
        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);

        const response = await fetch('/api/token/', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Invalid credentials'); // Prompt for credentials again
            } else {
                throw new Error('Network response was not ok'); // Handle other errors
            }
        }

        const data = await response.json();
        localStorage.setItem('authToken', data.access);
        console.log('Token stored successfully');
        return data.access;
    } catch (error) {
        console.error('Error during token fetch:', error);
        alert('Error fetching token: ' + error.message); // Alert user about the error
        return null;
    }
}

function promptForCredentials() {
    const email = prompt('Enter your email:');
    const password = prompt('Enter your password:');
    return { email, password };
}

async function setupWebSocket(authToken) {
    console.log('Setting up WebSocket');
    let url = `ws://${window.location.host}/ws/live_chat/?token=${authToken}`;
    console.log('WebSocket URL:', url);
    var ws = new WebSocket(url);
    let senderId = null;
        
    ws.onopen = (e) => {
        ws.send(JSON.stringify({ "loaded": true }));
    };

    ws.onerror = (e) => {
        console.log(e);
    };

    ws.onmessage = function(event) {
        const content = JSON.parse(event.data);
        console.log('Received:', content);
        switch (content.type) {
            case 'user_id':
                senderId = content.user_id;
                break;
            case 'chat_request_notification':
                displayChatRequest(content);
                break;
            case 'chat_message':
                displayChatMessage(content);
                break;
            case 'user_list':
                displayUserList(content.users);
                break;
            case 'chat_request_accepted':
                displaySystemMessage(content.message);
                break;
            case 'chat_request_denied':
                displaySystemMessage(content.message);
                break;
            case 'chat_history':
                displayChatHistory(content.messages);
                break;
        }
    };

    ws.onclose = async function(event) {
        if (event.code === 1006) {
            console.error('Token expired or authentication error');
            const credentials = promptForCredentials();
            if (credentials) {
                const newToken = await obtainAuthToken(credentials.email, credentials.password);
                if (newToken) {
                    setupWebSocket(newToken);
                } else {
                    // Handle failure to obtain new token (e.g., display error to user)
                    console.error('Failed to obtain new token');
                    displaySystemMessage('Failed to authenticate. Please try again.');
                }
            }
        } else {
            console.error('WebSocket closed:', event);
            // Handle other close codes if necessary
            displaySystemMessage(`WebSocket closed with code ${event.code}`);
        }
    };

    function displayChatRequest(content) {
        var requests = document.getElementById('chat-window');
        var requestItem = document.createElement('div');
        requestItem.textContent = `Chat request from ${content.sender_name}`;
        console.log(content);
        var acceptButton = createButton('Accept', content.sender_id, content.receiver_id, true);
        var denyButton = createButton('Deny', content.sender_id, content.receiver_id, false);
        requestItem.appendChild(acceptButton);
        requestItem.appendChild(denyButton);
        requests.appendChild(requestItem);
    }

    function createButton(text, senderId, receiverId, isAccept) {
        var button = document.createElement('button');
        button.textContent = text;
        console.log(senderId, receiverId);
        button.onclick = function() {
            ws.send(JSON.stringify({
                'type': isAccept ? 'chat_request_accepted' : 'chat_request_denied',
                'sender_id': senderId,
                'receiver_id': receiverId
            }));
            button.parentNode.remove();
        };
        return button;
    }

    function displayUserList(users) {
        var userListElement = document.getElementById('userList');
        userListElement.innerHTML = '';
        users.forEach(function(user) {
            var userItem = document.createElement('li');
            userItem.textContent = `${user.name}`;
            userItem.setAttribute('data-user-id', user.id);
            userItem.onmouseover = function() {
                userItem.style.cursor = 'pointer';
            };
            var requestButton = document.createElement('button');
            requestButton.textContent = 'Request Chat';
            requestButton.onclick = function() {
                sendChatRequest(user.id);
            };
            userItem.appendChild(requestButton);
            userListElement.appendChild(userItem);
        });
    }

    function sendChatRequest(receiverId) {
        ws.send(JSON.stringify({
            'type': 'chat_request',
            'receiver_id': receiverId,
            'sender_id': senderId
        }));
    }

    function sendChatHistoryRequest(senderId, receiverId) {
        ws.send(JSON.stringify({
            'type': 'chat_history',
            'sender_id': senderId,
            'receiver_id': receiverId
        }));
    }

    function displayChatMessage(content) {
        var messages = document.getElementById('chat-window');
        var messageItem = document.createElement('div');
        var messageText = document.createElement('span');
        var messageTimestamp = document.createElement('span');
        sendChatHistoryRequest(content.sender_id, content.receiver_id);
        messageText.textContent = `${content.sender_name}: ${content.message}`;
        messageTimestamp.textContent = ` (${new Date().toLocaleString()})`;
        messageTimestamp.classList.add('timestamp');

        // Determine alignment based on sender_id
        messageItem.classList.add('message-item');
        if (content.sender_id === senderId) {
            messageItem.classList.add('message-sender');
        } else {
            messageItem.classList.add('message-receiver');
        }

        messageItem.appendChild(messageText);
        messageItem.appendChild(messageTimestamp);
        messages.appendChild(messageItem);
        messages.scrollTop = messages.scrollHeight; // Scroll to bottom
    }

    function displaySystemMessage(message) {
        var messages = document.getElementById('chat-window');
        var messageItem = document.createElement('div');
        messageItem.textContent = message;
        messages.appendChild(messageItem);
        messages.scrollTop = messages.scrollHeight; // Scroll to bottom
    }

    // Display chat history with updated alignment
    function displayChatHistory(messages) {
        var chatWindow = document.getElementById('chat-window');
        messages.forEach(function(message) {
            var messageItem = document.createElement('div');
            var messageText = document.createElement('span');
            var messageTimestamp = document.createElement('span');
            messageText.textContent = message.sender_name + ': ' + message.message;
            messageTimestamp.textContent = ` (${new Date(message.timestamp).toLocaleString()})`;
            messageTimestamp.classList.add('timestamp');
            messageItem.classList.add('message-item');

            // Determine alignment based on sender_id
            if (message.sender_id === senderId) {
                messageItem.classList.add('message-sender');
                messageItem.style.textAlign = 'right'; // Align sender's messages to the right
            } else {
                messageItem.classList.add('message-receiver');
                messageItem.style.textAlign = 'left'; // Align receiver's messages to the left
            }

            messageItem.appendChild(messageText);
            messageItem.appendChild(messageTimestamp);
            chatWindow.appendChild(messageItem);
        });

        chatWindow.scrollTop = chatWindow.scrollHeight; // Scroll to bottom
    }

    // Use a single event listener for the "send" button
    document.getElementById("send").addEventListener('click', function() {
        var message = document.getElementById("message-text").value;
        var receiverId = document.getElementById("receiver-id").value;
        ws.send(JSON.stringify({
            'type': 'chat_message',
            'message': message,
            'sender_id': senderId,
            'receiver_id': receiverId
        }));
        sendChatHistoryRequest(senderId, receiverId);
    });
}

document.addEventListener("DOMContentLoaded", async function() {
    let authToken = localStorage.getItem('authToken');

    if (!authToken) {
        const credentials = promptForCredentials();
        if (credentials) {
            authToken = await obtainAuthToken(credentials.email, credentials.password);
        }
    }

    if (authToken) {
        setupWebSocket(authToken);
    } else {
        console.error('No auth token found in localStorage and failed to obtain new one');
    }
});
console.log('Chat script loaded');
