class ChatHandler {
  constructor() {
    this.ws = null;
    this.senderId = null;
    this.currentReceiverId = null;
    this.friendsList = [];
    this.onlineUserIds = [];
    this.router = null;
  }

  async init(params, router, context) {
      this.router = router;

      // console.log('Params:', params);
      const url = `ws://${window.location.host}/ws/live_chat/}`;
      // console.log('WebSocket URL:', url);

      if (this.ws) {
          console.log('Closing existing WebSocket connection');
          this.ws.close();
      }

      console.log('Creating new WebSocket connection');
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
          console.log('WebSocket connection opened');
          this.ws.send(JSON.stringify({ "type": 'set_context', "context": context }));
      };

      this.ws.onerror = (e) => {
          // console.error('WebSocket error:', e);
      };

      this.ws.onmessage = this.onMessage.bind(this);
      this.ws.onclose = (e) => this.onClose(e, context);

      if (context === 'chat') {
        this.currentReceiverId = params.username;
        this.chatWindowOpened = false;
      } else {
          this.currentReceiverId = null;
          this.initScrollHandling();
      }
    }

  async onClose(event, context) {
    console.log('WebSocket connection closed:', event.code, event.reason);
  }

  onMessage(event) {
    const content = JSON.parse(event.data);
    console.log('Received message:', content);
    if (content.type === 'user_id') {
      this.senderId = Number(content.user_id);
      console.log('Received user ID:', this.senderId, content.context);
      if (content.context === 'chat' && !this.chatWindowOpened) {
          // Open chat window only after receiving the user ID
          this.openChatWindow(this.currentReceiverId);
          this.chatWindowOpened = true;
      }
      return;
    }
    switch (content.context) {
      case 'home':
        this.handleHomeContext(content);
        break;
      case 'chat':
        this.handleChatContext(content);
        break;
      default:
        // console.error('Unknown context:', content.context);
        break;
    }
  }

  handleHomeContext(content) {
    switch (content.type) {
      case 'user_list':
        this.displayUserList(content.users);
        break;
      case 'friends_list':
        this.displayFriendsList(content.friends);
        break;
      case 'unread_counts':
        this.updateUnreadMessages(content);
        break;
      case 'chat_message':
        this.incrementUnreadMessageCount(content.sender_id);
        this.showLatestMessage(content.message, content.sender_id, content.sender_id);
        break;
      case 'message_preview':
        const friendItems = document.querySelectorAll('.friend-item');
        friendItems.forEach(friendItem => {
            const dataId = friendItem.getAttribute('data-id');
            if (content.latest_messages[dataId]) {
              const latestMessage = content.latest_messages[dataId].message;
              const sender_id = content.latest_messages[dataId].sender_id;
              if (latestMessage) {
                this.showLatestMessage(latestMessage, sender_id, dataId);
              }
            }
            else {
              console.log('No messages');
              const messagePreview = friendItem.querySelector('.message-preview');
              if (messagePreview) {
              messagePreview.textContent = 'No messages';
              }
            }
            });
        break;
      default:
        console.error('Error:', content.type);
        break;
    }
  }

  showLatestMessage(message, senderId, friendId) {
    const friendItem = document.querySelector(`.friend-item[data-id="${friendId}"]`);
    console.log(friendId);
    if (friendItem) {
      const messagePreview = friendItem.querySelector('.message-preview');
      if (messagePreview && message) {
        if (message.length > 30) {
          message = message.slice(0, 30) + '...';
        }
        console.log(this.senderId, senderId);
        if (senderId === this.senderId) {
          messagePreview.textContent = `You: ${message}`;
        } else {
          messagePreview.textContent = message;
        }
      } else {
        console.log('preview not found');
      }
    } else {
      console.warn('Friend item not found (latest message):', friendId);
    }
  }

  handleChatContext(content) {
    switch (content.type) {
      case 'chat_message':
        if (content.sender_id === this.currentReceiverId || content.receiver_id === this.currentReceiverId)
          this.displayChatMessage(content);
          break;
      case 'chat_history':
        this.displayChatHistory(content.messages);
        break;
      case 'error':
        this.displaySystemMessage(content.message);
        break;
      default:
        console.error('Error:', content.type);
        break;
    }
  }

  sendMessage(receiverId) {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (this.ws && message && receiverId && receiverId !== this.senderId) {
      console.log('Sending message to:', receiverId);
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
            console.log('Removing unread indicator');
            if (friendItem.contains(unreadIndicator)) {
                unreadIndicator.remove();
            }
        }
    });
  }

  incrementUnreadMessageCount(senderId) {
    const friendItem = document.querySelector(`.friend-item[data-id="${senderId}"]`);
    if (friendItem) {
      let unreadIndicator = friendItem.querySelector('.unread-indicator');
      if (!unreadIndicator) {
        unreadIndicator = document.createElement('div');
        unreadIndicator.className = 'unread-indicator';
      }
      const currentCount = Number(unreadIndicator.textContent) || 0;
      unreadIndicator.textContent = currentCount + 1;
      if (!friendItem.contains(unreadIndicator)) {
        friendItem.appendChild(unreadIndicator);
      }
    } else {
      console.warn('Friend item not found (unread messages):', senderId);
    }
  }

  // showMessageNotification(content) {
  //   this.updateUnreadMessageIndicator(content.sender_id);
  // }

  displayChatRequest(content) {
    const requests = document.getElementById('chat-window');
    if (requests) {
      const requestItem = document.createElement('div');
      requestItem.textContent = `Chat request from ${content.sender_name}`;
      // console.log(content);

      const acceptButton = this.createButton('Accept', content.sender_id, content.receiver_id, true);
      const denyButton = this.createButton('Deny', content.sender_id, content.receiver_id, false);

      requestItem.appendChild(acceptButton);
      requestItem.appendChild(denyButton);
      requests.appendChild(requestItem);
    } else {
      console.warn('Chat window not found');
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
    if (!userListContainer) {
      console.warn('User list container not found');
      return;
    }
    const userListWrapper = userListContainer.querySelector('.user-list-wrapper');
    
    if (!userListWrapper) {
      console.warn('User list wrapper not found');
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
    userListContainer.style.height = `${firstRowHeight + 20}px`;
  
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
        console.warn('Image not found for friend item:', friendId);
      }
    });
  }
  
  displayFriendsList(friends) {
    const friendListElement = document.querySelector('.friends-scroll-container');
    if (!friendListElement) {
      console.warn('Friend list container not found');
      return;
    }
  
    friendListElement.innerHTML = '';
  
    friends.forEach((friend) => {
      const friendItem = document.createElement('div');
      friendItem.className = 'friend-item';
      friendItem.setAttribute('data-id', friend.id);
      friendItem.onclick = () => {
        if (this.router) {
          const encodedId = encodeURIComponent(friend.id);
          this.router.navigate(`/live_chat/chat_room?user_id=${encodedId}`);
        } else {
          console.warn('Router instance is undefined');
          return;
        }
      };
  
      const friendImg = document.createElement('img');
      friendImg.src = friend.profile_picture_url;
      friendImg.alt = friend.name;
      friendImg.className = 'friend-avatar';
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
    });
    this.ws.send(JSON.stringify({
      'type': 'message_preview',
      'context': 'home'
    }));
  }

  openChatWindow(friendId) {
    this.ws.send(JSON.stringify({
      'type': 'message_read',
      'sender_id': this.senderId,
      'receiver_id': friendId
    }));
    const chatWindow = document.getElementById('chat-window');
    const chatTitle = document.getElementById('chat-title');
    const messagesContainer = document.getElementById('chat-messages');
    const closeButton = document.getElementById('close-chat');
    const sendButton = document.getElementById('send-message');
    const messageInput = document.getElementById('message-input');
  
    console.log('Opening chat window with friend ID:', friendId);
    chatTitle.textContent = `Chat with ${friendId}`;
    chatWindow.classList.add('open');
  
    // messagesContainer.innerHTML = '';
    messageInput.value = '';
    this.currentReceiverId = friendId;
    
    const storedMessages = localStorage.getItem(`chat_history_${this.senderId}_${friendId}`);
    if (storedMessages) {
      this.displayChatHistory(JSON.parse(storedMessages));
    } else {
      console.log('Requesting chat history for:', friendId, this.senderId);
      this.sendChatHistoryRequest(this.senderId, friendId);
    }
    sendButton.addEventListener('click', () => {
      console.log('Send button clicked');
      this.sendMessage(this.currentReceiverId);
    });
    closeButton.addEventListener('click', () => {
      console.log('Close button clicked');
      if (this.router) {
        this.router.navigate('/live_chat');
      }
    });
    messageInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.sendMessage(this.currentReceiverId);
      }
    });
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
      messages.scrollTop = messages.scrollHeight;
    } else {
      console.warn('Chat messages container not found');
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
      console.warn('Chat messages container not found');
    }
  }

  displaySystemMessage(message) {
    const messages = document.getElementById('chat-window');
    if (messages) {
      const messageItem = document.createElement('div');
      messageItem.textContent = message;
      messages.appendChild(messageItem);
    } else {
      console.warn('Chat window not found');
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
      console.warn('User list container not found');
    }
  }
}

const instance = new ChatHandler();
export default {
  getInstance() {
    return instance;
  }
};
