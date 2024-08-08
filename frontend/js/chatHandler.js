class ChatHandler {
  constructor() {
    this.ws = null;
    this.senderId = null;
    this.currentReceiverId = null;
    this.friendsList = [];
    this.onlineUserIds = [];
    this.router = null;
  }

  async init(authToken, params, router) {
    if (this.ws) {
      console.warn('WebSocket already initialized');
      return;
    }

    this.router = router;  // Save the router instance
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
    
    // Handle message sending on the chat page
    if (params && params.friendId) {
      this.currentReceiverId = params.friendId;
      document.getElementById('send-message').addEventListener('click', () => this.sendMessage(this.currentReceiverId));
    }

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
          if (content.sender_id === this.currentReceiverId || content.receiver_id === this.currentReceiverId)
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
        // this.updateLatestMessage(content.messages);
        break;
      case 'friends_list':
        this.displayFriendsList(content.friends);
        break;
      case 'unread_counts':
        this.updateUnreadMessages(content);
        break;
      case 'error':
        this.displaySystemMessage(content.message);
      default:
        console.error('Error:', content.type);
        break;
    }
  }

  sendMessage(receiverId) {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (this.ws && message && receiverId && receiverId !== this.senderId) {
      const newMessage = {
        'type': 'chat_message',
        'message': message,
        'sender_id': this.senderId,
        'receiver_id': receiverId,
        'timestamp': new Date().toISOString()
      };
      this.ws.send(JSON.stringify(newMessage));
      messageInput.value = '';
    } else {
      console.warn('Message, receiver ID is empty, or sender and receiver are the same');
    }
  }

  updateUnreadMessages(content) {
    const friendItems = document.querySelectorAll('.friend-item');
    friendItems.forEach(friendItem => {
        const senderId = friendItem.getAttribute('data-id');
        let unreadIndicator = friendItem.querySelector('.unread-indicator');
        if (!unreadIndicator) {
            unreadIndicator = document.createElement('div');
            unreadIndicator.className = 'unread-indicator';
        }

        const unreadCount = content.unread_messages[senderId] || 0;
        if (unreadCount > 0) {
            unreadIndicator.textContent = unreadCount;
            if (!friendItem.contains(unreadIndicator)) {
                friendItem.appendChild(unreadIndicator);
            }
        } else {
            if (friendItem.contains(unreadIndicator)) {
                unreadIndicator.remove();
            }
        }
    });
}

  // showMessageNotification(content) {
  //   this.updateUnreadMessageIndicator(content.sender_id);
  // }

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
    const userListContainer = document.getElementById('user-list-container');
    const userListWrapper = userListContainer.querySelector('.user-list-wrapper');
    
    if (!userListWrapper) {
      console.error('User list wrapper not found');
      return;
    }
  
    userListWrapper.innerHTML = '';
  
    this.onlineUserIds = users.map(user => user.id);

    users.forEach((user) => {
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
      // userItem.onclick = () => this.openChatModal(user.id, user.name);
  
      userListWrapper.appendChild(userItem);
    });
  
    const firstRowHeight = userListWrapper.children[0]?.offsetHeight || 0;
    userListContainer.style.height = `${firstRowHeight + 20}px`; // Add some padding
  
    if (userListWrapper.offsetHeight > userListContainer.offsetHeight) {
      userListContainer.style.overflowY = 'auto';
    } else {
      userListContainer.style.overflowY = 'hidden';
    }
    this.updateFriendStatusIndicators();
  }

  updateFriendStatusIndicators() {
    const friendItems = document.querySelectorAll('.friend-item');
    friendItems.forEach(friendItem => {
      const friendId = friendItem.getAttribute('data-id');
      
      const isOnline = this.onlineUserIds.includes(friendId);
  
      const friendImg = friendItem.querySelector('img');
  
      if (friendImg) {
        friendImg.style.border = isOnline ? '4px solid #7A35EC' : '4px solid grey';
      } else {
        console.error('Image not found for friend item:', friendId);
      }
    });
  }
  
  displayFriendsList(friends) {
    const friendListElement = document.querySelector('.friends-scroll-container');
    if (!friendListElement) {
      console.error('Friend list container not found');
      return;
    }
  
    friendListElement.innerHTML = '';
  
    friends.forEach((friend) => {
      const friendItem = document.createElement('div');
      friendItem.className = 'friend-item';
      friendItem.setAttribute('data-id', friend.id);
  
      const friendImg = document.createElement('img');
      friendImg.src = friend.profile_picture_url;
      friendImg.alt = friend.name;
      friendImg.className = 'friend-avatar';
      friendImg.onclick = () => this.openChatWindow(friend.id, friend.name);
  
      const friendInfo = document.createElement('div');
      friendInfo.className = 'friend-info';
  
      const friendName = document.createElement('div');
      friendName.className = 'friend-name';
      friendName.textContent = friend.name;
  
      const messagePreview = document.createElement('div');
      messagePreview.className = 'message-preview';
      messagePreview.textContent = 'Loading...';
  
      friendInfo.appendChild(friendName);
      friendInfo.appendChild(messagePreview);
  
      friendItem.appendChild(friendImg);
      friendItem.appendChild(friendInfo);
  
      friendListElement.appendChild(friendItem);
  
      this.sendChatHistoryRequest(this.senderId, friend.id)
        .then(messages => {
          if (messages && messages.length > 0) {
            console.log('Latest message:', messages[messages.length - 1]);
            const latestMessage = messages[messages.length - 1];
            const previewText = latestMessage.message.length > 30 
              ? latestMessage.message.substring(0, 30) + '...' 
              : latestMessage.message;
            messagePreview.textContent = previewText;
          } else {
            messagePreview.textContent = 'No messages yet';
          }
        })
        .catch(error => {
          console.error('Error fetching chat history:', error);
          messagePreview.textContent = 'Error loading messages';
        });
    });
  }

  openChatWindow(friendId, friendName) {
    const chatWindow = document.getElementById('chat-window');
    const chatTitle = document.getElementById('chat-title');
    const messagesContainer = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const closeButton = document.getElementById('close-chat');
    const sendButton = document.getElementById('send-message');
  
    chatTitle.textContent = `Chat with ${friendName}`;
    chatWindow.classList.add('open');
  
    messagesContainer.innerHTML = '';
    messageInput.value = '';
    this.currentReceiverId = friendId;
  
    // Load chat history from localStorage
    const storedMessages = localStorage.getItem(`chat_history_${this.senderId}_${friendId}`);
    if (storedMessages) {
      this.displayChatHistory(JSON.parse(storedMessages));
    } else {
      this.sendChatHistoryRequest(this.senderId, friendId);
    }
  
    closeButton.onclick = () => this.closeChatWindow();
    sendButton.onclick = () => this.sendMessage(friendId);
    messageInput.onkeypress = (e) => {
      if (e.key === 'Enter') {
        this.sendMessage(friendId);
      }
    };
  
    if (this.router) {
      const encodedName = encodeURIComponent(friendName);
      this.router.navigate(`/live_chat/${encodedName}`);
    } else {
      console.error('Router instance is undefined');
    }
  }
  
  
  closeChatWindow() {
    const chatWindow = document.getElementById('chat-window');
    const friendsListContainer = document.getElementById('friends-list-container');
    const mainContent = document.querySelector('.main-content');
    const messageInput = document.getElementById('message-input');
  
    mainContent.classList.remove('chat-open');
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

        localStorage.setItem(`chat_history_${this.senderId}_${this.currentReceiverId}`, JSON.stringify(messages));
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

  removeFriend(friendId) {
    if (this.ws && friendId) {
      this.ws.send(JSON.stringify({
        'type': 'update_status',
        'user_id_1': friendId,
        'user_id_2': this.senderId,
        'status': 'DF'

      }));
    } else {
      console.warn('Cannot remove friend, WebSocket is not initialized or friend ID is missing');
    }
  }

  sendChatHistoryRequest(senderId, receiverId) {
    return new Promise((resolve, reject) => {
      if (this.ws && senderId && receiverId) {
        const requestId = Date.now().toString();
  
        const messageHandler = (event) => {
          const content = JSON.parse(event.data);
          if (content.type === 'chat_history' && content.sender_id === senderId && content.receiver_id === receiverId) {
            this.ws.removeEventListener('message', messageHandler);
            resolve(content.messages);
          }
        };
  
        this.ws.addEventListener('message', messageHandler);
  
        this.ws.send(JSON.stringify({
          'type': 'chat_history',
          'sender_id': senderId,
          'receiver_id': receiverId,
          'request_id': requestId
        }));
  
        setTimeout(() => {
          this.ws.removeEventListener('message', messageHandler);
          reject(new Error('Chat history request timed out'));
        }, 5000);
      } else {
        reject(new Error('Cannot request chat history, WebSocket is not initialized or IDs are missing'));
      }
    });
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
