class ChatHandler {
  constructor() {
    this.ws = null;
    this.senderId = null;
    this.currentReceiverId = null;
    this.friendsList = [];
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

    document.getElementById('send-message').addEventListener('click', () => this.sendMessage());

    this.initScrollHandling();
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
        if (content.receiver_id === this.currentReceiverId) {
          this.displayChatMessage(content);
        }
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
      case 'friends_list':
        this.displayFriendsList(content.friends);
      default:
        console.error('Unknown message type:', content.type);
        break;
    }
  }

  sendMessage(receiverId) {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();

    if (this.ws && message && receiverId && receiverId !== this.senderId) {
      this.ws.send(JSON.stringify({
        'type': 'chat_message',
        'message': message,
        'sender_id': this.senderId,
        'receiver_id': receiverId
      }));
      messageInput.value = ''; // Clear input field
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
    const userListElement = document.getElementById('user-list-container');
    
    if (!userListElement) {
      console.error('User list container not found');
      return;
    }
  
    userListElement.innerHTML = '';
  
    users.slice(0, 10).forEach((user) => {
      const userItem = document.createElement('div');
      userItem.className = 'user-item';
  
      const userImg = document.createElement('img');
      userImg.src = user.profile_picture_url;
      userImg.alt = user.name;
      userImg.className = 'user-avatar';
  
      const userName = document.createElement('div');
      userName.className = 'username';
      userName.textContent = user.name;
  
      userItem.appendChild(userImg);
      userItem.appendChild(userName);
  
      userItem.onclick = () => this.openChatModal(user.id, user.name);
  
      userListElement.appendChild(userItem);
    });
  }
  

  displayFriendsList(friends) {
    const friendListElement = document.getElementById('friends-list-container');
    
    if (!friendListElement) {
      console.error('Friend list container not found');
      return;
    }
  
    friendListElement.innerHTML = '';
  
    friends.forEach((friend) => {
      const friendItem = document.createElement('div');
      friendItem.className = 'friend-item';
  
      const friendImg = document.createElement('img');
      friendImg.src = friend.profile_picture_url;
      friendImg.alt = friend.name;
      friendImg.className = 'friend-avatar';
  
      const friendName = document.createElement('div');
      friendName.className = 'friend-name';
      friendName.textContent = friend.name;
  
      friendItem.appendChild(friendImg);
      friendItem.appendChild(friendName);
  
      friendItem.onclick = () => this.openChatWindow(friend.id, friend.name);
  
      friendListElement.appendChild(friendItem);
    });
  }

  openChatWindow(friendId, friendName) {
    const chatWindow = document.getElementById('chat-window');
    const friendsListContainer = document.getElementById('friends-list-container');
    const chatTitle = document.getElementById('chat-title');
    const closeButton = document.getElementById('close-chat');
    const sendButton = document.getElementById('send-message');
    const messageInput = document.getElementById('message-input');
  
    chatTitle.textContent = `Chat with ${friendName}`;
  
    chatWindow.classList.add('open');
    friendsListContainer.classList.add('chat-open');
  
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';
  
    messageInput.value = '';
  
    this.currentReceiverId = friendId;
  
    this.sendChatHistoryRequest(this.senderId, friendId);
  
    closeButton.onclick = () => this.closeChatWindow();
    sendButton.onclick = () => this.sendMessage(friendId);
    messageInput.onkeypress = (e) => {
      if (e.key === 'Enter') {
        this.sendMessage(friendId);
      }
    };
  }
  
  closeChatWindow() {
    const chatWindow = document.getElementById('chat-window');
    const friendsListContainer = document.getElementById('friends-list-container');
    const messageInput = document.getElementById('message-input');
  
    chatWindow.classList.remove('open');
    friendsListContainer.classList.remove('chat-open');
  
    messageInput.value = '';
  
    this.currentReceiverId = null;
  }
  

  displayChatMessage(content) {
    const messages = document.getElementById('chat-messages');
    if (messages) {
      const messageItem = document.createElement('div');
      messageItem.className = 'chat-message';

      const messageText = document.createElement('span');
      messageText.className = 'message-text';
      messageText.textContent = `${content.sender_name}: ${content.message}`;

      const messageTimestamp = document.createElement('span');
      messageTimestamp.className = 'message-timestamp';
      messageTimestamp.textContent = ` (${new Date().toLocaleTimeString()})`;

      messageItem.appendChild(messageText);
      messageItem.appendChild(messageTimestamp);
      
      messages.appendChild(messageItem);
      messages.scrollTop = messages.scrollHeight; // Auto-scroll to bottom
    } else {
      console.error('Chat messages container not found');
    }
  }

  displayChatHistory(messages) {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
      chatMessages.innerHTML = '';
      messages.forEach((message) => {
        const messageItem = document.createElement('div');
        messageItem.className = 'chat-message';
  
        const messageText = document.createElement('span');
        messageText.className = 'message-text';
        messageText.textContent = `${message.sender_name}: ${message.message}`;
  
        const messageTimestamp = document.createElement('span');
        messageTimestamp.className = 'message-timestamp';
        messageTimestamp.textContent = ` (${new Date(message.timestamp).toLocaleTimeString()})`;
  
        messageItem.appendChild(messageText);
        messageItem.appendChild(messageTimestamp);
        
        chatMessages.appendChild(messageItem);
      });
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
      console.error('Chat messages container not found');
    }
  }

  displaySystemMessage(message) {
    const messages = document.getElementById('chat-window');
    if (messages) {
      const messageItem = document.createElement('div');
      messageItem.textContent = message;
      messages.appendChild(messageItem);
    } else {
      console.error('Chat window not found');
    }
  }

  sendChatHistoryRequest(senderId, receiverId) {
    if (this.ws && senderId && receiverId) {
      this.ws.send(JSON.stringify({
        'type': 'chat_history_request',
        'sender_id': senderId,
        'receiver_id': receiverId
      }));
    } else {
      console.warn('Cannot request chat history, WebSocket is not initialized or IDs are missing');
    }
  }

  initScrollHandling() {
    const container = document.querySelector('.user-list-container');

    if (container) {
      container.addEventListener('wheel', (event) => {
        // Check if Ctrl key is pressed
        if (event.ctrlKey) {
          // Allow browser default zoom behavior
          return;
        }

        // Horizontal scrolling
        if (event.deltaY !== 0) {
          container.scrollLeft += event.deltaY;
          event.preventDefault(); // Prevent the default vertical scroll behavior
        }
      });
    } else {
      console.error('User list container not found');
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
