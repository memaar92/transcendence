class ChatHandler {
  constructor() {
    this.ws = null;
    this.senderId = null;
  }

  async init(authToken) {
    if (this.ws) {
      console.warn('WebSocket already initialized');
      return;
    }

    const url = `ws://${window.location.host}/ws/live_chat/?token=${authToken}`;
    console.log('WebSocket URL:', url);

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.ws.send(JSON.stringify({ "loaded": true }));
    };

    this.ws.onerror = (e) => {
      console.error('WebSocket error:', e);
    };

    this.ws.onmessage = this.onMessage.bind(this);
    this.ws.onclose = this.onClose.bind(this);

    const sendButton = document.getElementById("send");
    if (sendButton) {
      sendButton.addEventListener('click', () => this.sendMessage());
    } else {
      console.error('Send button not found');
    }
  }

  async onClose(event) {
    if (event.code === 1006) {
      console.error('Token expired or authentication error');
      const credentials = promptForCredentials();
      if (credentials) {
        const newToken = await obtainAuthToken(credentials.email, credentials.password);
        if (newToken) {
          this.init(newToken);
        } else {
          console.error('Failed to obtain new token');
          this.displaySystemMessage('Failed to authenticate. Please try again.');
        }
      }
    } else {
      console.error('WebSocket closed:', event);
      this.displaySystemMessage(`WebSocket closed with code ${event.code}`);
    }
  }

  onMessage(event) {
    const content = JSON.parse(event.data);
    console.log('Received:', content);

    switch (content.type) {
      case 'user_id':
        this.senderId = content.user_id;
        break;
      case 'chat_request_notification':
        this.displayChatRequest(content);
        break;
      case 'chat_message':
        this.displayChatMessage(content);
        break;
      case 'user_list':
        this.displayUserList(content.users);
        break;
      case 'chat_request_accepted':
        this.displaySystemMessage(content.message);
        break;
      case 'chat_request_denied':
        this.displaySystemMessage(content.message);
        break;
      case 'chat_history':
        this.displayChatHistory(content.messages);
        break;
      default:
        console.error('Unknown message type:', content.type);
        break;
    }
  }

  sendMessage() {
    const message = document.getElementById("message-text").value;
    const receiverId = document.getElementById("receiver-id").value;

    if (this.ws && message.trim() && receiverId.trim() && receiverId !== this.senderId) {
      this.ws.send(JSON.stringify({
        'type': 'chat_message',
        'message': message,
        'sender_id': this.senderId,
        'receiver_id': receiverId
      }));
      this.sendChatHistoryRequest(this.senderId, receiverId);
      document.getElementById("message-text").value = ''; // Clear message input
    } else {
      console.warn('Message, receiver ID is empty, or sender and receiver are the same');
    }
  }

  displayChatRequest(content) {
    const requests = document.getElementById('chat-window');
    if (requests) {
      const requestItem = document.createElement('div');
      requestItem.textContent = `Chat request from ${content.sender_name}`;
      console.log(content);

      const acceptButton = this.createButton('Accept', content.sender_id, content.receiver_id, true);
      const denyButton = this.createButton('Deny', content.sender_id, content.receiver_id, false);

      requestItem.appendChild(acceptButton);
      requestItem.appendChild(denyButton);
      requests.appendChild(requestItem);
    } else {
      console.error('Chat window not found');
    }
  }

  createButton(text, senderId, receiverId, isAccept) {
    const button = document.createElement('button');
    button.textContent = text;

    button.onclick = () => {
      this.ws.send(JSON.stringify({
        'type': isAccept ? 'chat_request_accepted' : 'chat_request_denied',
        'sender_id': senderId,
        'receiver_id': receiverId
      }));
      button.parentNode.remove();
    };
    return button;
  }

  displayUserList(users) {
    const userListElement = document.getElementById('userList');
    if (userListElement) {
      userListElement.innerHTML = ''; // Clear existing user list
  
      users.forEach((user) => {
        const userItem = document.createElement('li');
        userItem.textContent = `${user.name}`;
        userItem.style.marginBottom = '10px'; // Add spacing between items
        userItem.style.display = 'flex';
        userItem.style.justifyContent = 'space-between';
        userItem.style.alignItems = 'center';
  
        const requestButton = document.createElement('button');
        requestButton.textContent = 'Request Chat';
        requestButton.style.marginLeft = '10px'; // Add spacing between name and button
        requestButton.onclick = () => {
          this.sendChatRequest(user.id);
        };
  
        userItem.appendChild(requestButton);
        userListElement.appendChild(userItem);
      });
    } else {
      console.error('User list element not found');
    }
  }  

  sendChatRequest(receiverId) {
    if (this.ws && receiverId !== this.senderId) {
      this.ws.send(JSON.stringify({
        'type': 'chat_request',
        'receiver_id': receiverId,
        'sender_id': this.senderId
      }));
    } else {
      console.warn('Receiver ID is the same as sender ID');
    }
  }

  sendChatHistoryRequest(senderId, receiverId) {
    if (this.ws) {
      this.ws.send(JSON.stringify({
        'type': 'chat_history',
        'sender_id': senderId,
        'receiver_id': receiverId
      }));
    }
  }

  displayChatMessage(content) {
    const messages = document.getElementById('chat-window');
    if (messages) {
      const messageItem = document.createElement('div');
      const messageText = document.createElement('span');
      const messageTimestamp = document.createElement('span');
      
      messageText.textContent = `${content.sender_name}: ${content.message}`;
      messageTimestamp.textContent = ` (${new Date().toLocaleString()})`;
      messageTimestamp.classList.add('timestamp');

      messageItem.classList.add('message-item');
      if (content.sender_id === this.senderId) {
        messageItem.classList.add('message-sender');
      } else {
        messageItem.classList.add('message-receiver');
      }

      messageItem.appendChild(messageText);
      messageItem.appendChild(messageTimestamp);
      messages.appendChild(messageItem);
      messages.scrollTop = messages.scrollHeight; // Scroll to bottom
    } else {
      console.error('Chat window not found');
    }
  }

  displaySystemMessage(message) {
    const messages = document.getElementById('chat-window');
    if (messages) {
      const messageItem = document.createElement('div');
      messageItem.textContent = message;
      messages.appendChild(messageItem);
      messages.scrollTop = messages.scrollHeight;
    } else {
      console.error('Chat window not found');
    }
  }

  displayChatHistory(messages) {
    const chatWindow = document.getElementById('chat-window');
    if (chatWindow) {
      // Clear the chat window before appending new messages
      chatWindow.innerHTML = '';

      messages.forEach((message) => {
        const messageItem = document.createElement('div');
        const messageText = document.createElement('span');
        const messageTimestamp = document.createElement('span');
        
        messageText.textContent = `${message.sender_name}: ${message.message}`;
        messageTimestamp.textContent = ` (${new Date(message.timestamp).toLocaleString()})`;
        messageTimestamp.classList.add('timestamp');

        messageItem.classList.add('message-item');
        if (message.sender_id === this.senderId) {
          messageItem.classList.add('message-sender');
          messageItem.style.textAlign = 'right'; 
        } else {
          messageItem.classList.add('message-receiver');
          messageItem.style.textAlign = 'left';
        }    

        messageItem.appendChild(messageText);
        messageItem.appendChild(messageTimestamp);
        chatWindow.appendChild(messageItem);
      });
      
      chatWindow.scrollTop = chatWindow.scrollHeight; // Scroll to bottom
    } else {
      console.error('Chat window not found');
    }
  }
}

// Function to obtain a new authentication token
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
        throw new Error('Invalid credentials');
      } else {
        throw new Error('Network response was not ok');
      }
    }

    const data = await response.json();
    localStorage.setItem('authToken', data.access);
    console.log('Token stored successfully');
    return data.access;
  } catch (error) {
    console.error('Error during token fetch:', error);
    alert('Error fetching token: ' + error.message);
    return null;
  }
}

// Function to prompt the user for credentials
function promptForCredentials() {
  const email = prompt('Enter your email:');
  const password = prompt('Enter your password:');
  return { email, password };
}

const instance = new ChatHandler();
export default {
  getInstance() {
    return instance;
  }
};
