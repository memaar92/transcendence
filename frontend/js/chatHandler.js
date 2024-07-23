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
  
      let url = `ws://${window.location.host}/ws/live_chat/?token=${authToken}`;
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
        sendButton.addEventListener('click', this.sendMessage.bind(this));
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
  
      if (this.ws && message.trim() && receiverId.trim()) {
        this.ws.send(JSON.stringify({
          'type': 'chat_message',
          'message': message,
          'sender_id': this.senderId,
          'receiver_id': receiverId
        }));
        this.sendChatHistoryRequest(this.senderId, receiverId);
        document.getElementById("message-text").value = ''; // Clear message input
      } else {
        console.warn('Message or receiver ID is empty');
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
        userListElement.innerHTML = '';
        users.forEach((user) => {
          const userItem = document.createElement('li');
          userItem.textContent = `${user.name}`;
          userItem.setAttribute('data-user-id', user.id);
          userItem.onmouseover = () => {
            userItem.style.cursor = 'pointer';
          };
  
          const requestButton = document.createElement('button');
          requestButton.textContent = 'Request Chat';
          requestButton.onclick = () => {
            this.sendChatRequest(user.id);
          };
  
          userItem.appendChild(requestButton);
          userListElement.appendChild(userItem);
        });
      } else {
        console.error('User list not found');
      }
    }
  
    sendChatRequest(receiverId) {
      if (this.ws) {
        this.ws.send(JSON.stringify({
          'type': 'chat_request',
          'receiver_id': receiverId,
          'sender_id': this.senderId
        }));
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
  
        this.sendChatHistoryRequest(content.sender_id, content.receiver_id);
  
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
        messages.scrollTop = messages.scrollHeight;
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
  
        chatWindow.scrollTop = chatWindow.scrollHeight;
      } else {
        console.error('Chat window not found');
      }
    }
  }
  
  const instance = new ChatHandler();
  export default {
    getInstance() {
      return instance;
    }
  };
  