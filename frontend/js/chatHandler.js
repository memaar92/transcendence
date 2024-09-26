class ChatHandler {
  constructor() {
    this.ws = null;
    this.senderId = null;
    this.currentReceiverId = null;
    this.onlineUserIds = [];
    this.router = null;
    this.currentFilter = 'all';
  }

  async init(params, router, context) {
      this.router = router;

      // console.log('Params:', params);
      const url = `wss://${window.location.host}/ws/live_chat/}`;
      // console.log('WebSocket URL:', url);

      if (this.ws) {
          console.log('Closing existing WebSocket connection');
          this.ws.close();
      }

      console.log('Creating new WebSocket connection');
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
          console.log('WebSocket connection opened');
          this.ws.send(JSON.stringify({ "type": context, "context": 'setup' }));
          if (context === 'chat') {
            this.chatWindowOpened = false;
          }
      };

      this.ws.onerror = (e) => {
          // console.error('WebSocket error:', e);
      };

      this.ws.onmessage = this.onMessage.bind(this);
      this.ws.onclose = (e) => this.onClose(e, context);

      if (context === 'chat') {
        this.currentReceiverId = params.recipient;
        this.chatWindowOpened = false;
      } else {
          this.currentReceiverId = null;
          this.initScrollHandling();
          this.initFiltering();
      }
    }

  async onClose(event) {
    console.log('WebSocket connection closed:', event.code, event.reason);
  }

  onMessage(event) {
    const content = JSON.parse(event.data);
    console.log('Received message:', content);
    if (content.type === 'user_id') {
      this.senderId = Number(content.user_id);
      if (content.context === 'chat' && !this.chatWindowOpened) {
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
        this.displayChatsList(content.friends);
        break;
      case 'unread_counts':
        this.updateUnreadMessages(content);
        break;
      case 'chat_message':
        /* if there is not chats item with the receiver id, create one from the id, img url and name of the corresponding friend object */
        if (!document.querySelector(`.chats-item[data-id="${content.sender_id}"]`)) {
          const friendItem = document.querySelector(`.friends-item[data-id="${content.sender_id}"]`);
          if (friendItem) {
            const friend = {
            id: friendItem.getAttribute('data-id'),
            name: friendItem.getAttribute('data-name'),
            profile_picture_url: friendItem.querySelector('img').src
            };
            document.querySelector('.chats-scroll-container').appendChild(this.createChatItem(friend));
            const chatItem = document.querySelector(`.chats-item[data-id="${content.sender_id}"]`);
            if (chatItem) {
              const img = chatItem.querySelector('img');
              if (img) {
                img.style.border = '4px solid #7A35EC';
              }
            }
          } else {
            console.warn('Friend not found for sender ID:', content.sender_id);
          }
        }
        this.incrementUnreadMessageCount(content.sender_id);
        this.showLatestMessage(content.message, content.sender_id, content.sender_id);
        break;
      case 'request_status':
        this.displayModal(content);
        break;
      case 'message_preview':
        const chatItems = document.querySelectorAll('.chats-item');
        chatItems.forEach(chatItem => {
          const dataId = chatItem.getAttribute('data-id');
          if (content.latest_messages[dataId]) {
            const latestMessage = content.latest_messages[dataId].message;
            const sender_id = content.latest_messages[dataId].sender_id;
            if (latestMessage) {
              this.showLatestMessage(latestMessage, sender_id, dataId);
            }
          } else {
            console.log('No messages');
            const messagePreview = chatItem.querySelector('.message-preview');
            if (messagePreview) {
              messagePreview.textContent = 'No messages';
            }
          }
        });
        break;
      case "pending_requests":
        this.displayChatRequest(content.requests);
        break;
      default:
        console.error('Unknown context:', content.type);
        break;
    }
  }

  showLatestMessage(message, senderId, friendId) {
    if (document.querySelector('.no-chats-message')) {
      document.querySelector('.no-chats-message').remove();
    }
    const chatItem = document.querySelector(`.chats-item[data-id="${friendId}"]`);
    console.log(friendId);
    if (chatItem) {
      const messagePreview = chatItem.querySelector('.message-preview');
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
        this.displayChatMessage(content, 'received');
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

  displayModal(content) {
    // Create the modal container
    const modalContainer = document.createElement('div');
    modalContainer.className = 'modal fade';

    // Extract the username from the message (last word in the string)
    const usernameMatch = content.message.match(/(\b\w+\b)$/);
    const username = usernameMatch ? usernameMatch[0] : 'User';
    const messageWithHighlightedUsername = content.message.replace(username, `<span style="color: #0083e8;">${username}</span>`);

    // Define the full modal structure
    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Friend Request Accepted!</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            ${messageWithHighlightedUsername} ...
          </div>
        </div>
      </div>
    `;

    // Append the modal container to the body
    document.body.prepend(modalContainer);

    let modalInstance;
    try {
      modalInstance = new bootstrap.Modal(modalContainer, {
        keyboard: true,
        backdrop: 'static'
      });
      modalInstance.show();
    } catch (error) {
      console.error('Error initializing modal:', error);
      modalContainer.remove();
      return;
    }

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        modalInstance.hide();
      }
    };

    document.addEventListener('keydown', handleEscapeKey);

    // Clean up event listeners and modal instance when the modal is hidden
    modalContainer.addEventListener('hidden.bs.modal', () => {
      modalContainer.remove();
      modalInstance.dispose();
      document.removeEventListener('keydown', handleEscapeKey);
    });
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
      this.displayChatMessage(newMessage, 'sent');
    } else {
      console.warn('Message, receiver ID is empty, or sender and receiver are the same');
    }
  }

  updateUnreadMessages(content) {
    const chatItems = document.querySelectorAll('.chats-item');
    chatItems.forEach(chatItem => {
        const senderId = chatItem.getAttribute('data-id');
        let unreadIndicator = chatItem.querySelector('.unread-indicator');
        if (!unreadIndicator) {
            unreadIndicator = document.createElement('div');
            unreadIndicator.className = 'unread-indicator';
        }

        const unreadCount = content.unread_messages[senderId] || 0;
        if (unreadCount > 0) {
            unreadIndicator.textContent = unreadCount;
            if (!chatItem.contains(unreadIndicator)) {
                chatItem.appendChild(unreadIndicator);
            }
        } else {
            console.log('Removing unread indicator');
            if (chatItem.contains(unreadIndicator)) {
                unreadIndicator.remove();
            }
        }
    });
  }

  incrementUnreadMessageCount(senderId) {
    const chatItem = document.querySelector(`.chats-item[data-id="${senderId}"]`);
    if (chatItem) {
      let unreadIndicator = chatItem.querySelector('.unread-indicator');
      if (!unreadIndicator) {
        unreadIndicator = document.createElement('div');
        unreadIndicator.className = 'unread-indicator';
      }
      const currentCount = Number(unreadIndicator.textContent) || 0;
      unreadIndicator.textContent = currentCount + 1;
      if (!chatItem.contains(unreadIndicator)) {
        chatItem.appendChild(unreadIndicator);
      }
    } else {
      console.warn('Friend item not found (unread messages):', senderId);
    }
  }

  // showMessageNotification(content) {
  //   this.updateUnreadMessageIndicator(content.sender_id);
  // }

  /* add request items to the friends-scroll-container and requests filter */
  displayChatRequest(requests) {
    const requestsListElement = document.querySelector('.friends-scroll-container');
    requests.forEach((request) => {
      const requestItem = document.createElement('div');
      requestItem.className = 'friends-item requests';
      requestItem.setAttribute('data-id', request.requester_id);
      requestItem.setAttribute('data-name', request.requester_name);

      const requestName = document.createElement('div');
      requestName.className = 'request-name';
      requestName.textContent = request.requester_name;

      const requestMsg = document.createElement('div');
      requestMsg.className = 'request-msg';
      requestMsg.textContent = ' wants to be friends with you';

      const buttonsContainer = document.createElement('div');
      buttonsContainer.className = 'request-buttons';
      const acceptButton = this.createButton('Accept', request.requester_id, this.senderId, true);
      const denyButton = this.createButton('Deny', request.requester_id, this.senderId, false);

      buttonsContainer.appendChild(acceptButton);
      buttonsContainer.appendChild(denyButton);

      requestItem.appendChild(requestName);
      requestItem.appendChild(requestMsg);
      requestItem.appendChild(buttonsContainer);
  
      requestsListElement.appendChild(requestItem);
    });
    this.applyFilter();
  }

  createButton(text, senderId, receiverId, isAccept) {
    const button = document.createElement('button');
    if (!isAccept)
      button.className = 'mainButton reject';
    else 
      button.className = 'mainButton';
    button.textContent = text;

    button.onclick = () => {
      this.ws.send(JSON.stringify({
        'type': isAccept ? 'chat_request_accepted' : 'chat_request_denied',
        'sender_id': senderId,
        'receiver_id': receiverId
      }));
      button.parentNode.parentNode.remove();
    };
    return button;
  }

  updateUserRelationship(senderId, receiverId, status) {
    this.ws.send(JSON.stringify({
      'type': 'update_status',
      'sender_id': senderId,
      'receiver_id': receiverId,
      'status': status
    }));
  }
  
  blockFriend(senderId, receiverId) {
    this.updateUserRelationship(senderId, receiverId, 'BL');
    
    const friendItem = document.querySelector(`.friends-item[data-id="${receiverId}"]`);
  
    if (friendItem) {
      friendItem.classList.add('blocked');
      friendItem.classList.remove('friends');
      
      // Remove the chat button
      const chatButton = friendItem.querySelector('#chat-button');
      if (chatButton) {
        chatButton.remove();
      }
  
      // Update the block button to unblock button
      const blockButton = friendItem.querySelector('.mainButton.reject');
      if (blockButton) {
        blockButton.textContent = 'Unblock';
        blockButton.classList.replace('reject', 'unblock');
        blockButton.onclick = () => {
          this.unblockFriend(senderId, receiverId);
        };
      }
    }
    
    this.applyFilter();
  }

  unblockFriend(senderId, receiverId) {
    this.updateUserRelationship(senderId, receiverId, 'BF');
    
    const friendItem = document.querySelector(`.friends-item[data-id="${receiverId}"]`);
    
    if (friendItem) {
      friendItem.classList.remove('blocked');
      friendItem.classList.add('friends');
      
      // Remove the unblock button
      const unblockButton = friendItem.querySelector('.mainButton.unblock');
      if (unblockButton) {
        unblockButton.remove();
      }
  
      // Re-add the necessary buttons using createFriendsFilterButtons
      const friend = {
        id: receiverId,
        name: friendItem.getAttribute('data-name')
      };
      const buttons = this.createFriendsFilterButtons(friend);
      buttons.forEach(button => friendItem.appendChild(button));
    }
    
    this.applyFilter();
  }

  displayUserList(data) {
    console.log('Displaying user list');
    const parsedData = JSON.parse(data);
    const users = parsedData.users;
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
    
    this.onlineUserIds = users.map(user => user.id);
    userListWrapper.innerHTML = '';
  

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
    const chatItems = document.querySelectorAll('.chats-item');
    chatItems.forEach(chatItem => {
      const friendId = chatItem.getAttribute('data-id');
      const isOnline = this.onlineUserIds.includes(friendId);
      const friendImg = chatItem.querySelector('img');
      if (friendImg) {
        friendImg.style.border = isOnline ? '4px solid #7A35EC' : '4px solid grey';
        }
      else {
        console.warn('Image not found for chat item:', friendId);
      }
    });
  
    const friendItems = document.querySelectorAll('.friends-item');
    friendItems.forEach(friendItem => {
      if (!friendItem.classList.contains('requests')) { // Check if the item does not have the 'requests' class
        const friendId = friendItem.getAttribute('data-id');
        const isOnline = this.onlineUserIds.includes(friendId);
        const friendImg = friendItem.querySelector('img');
        if (friendImg) {
          friendImg.style.border = isOnline ? '4px solid #7A35EC' : '4px solid grey';
        }
        else {
          console.warn('Image not found for friend item:', friendId);
        }
      }
    });
  }

  createChatItem(friend) {
    const chatItem = document.createElement('div');
    chatItem.className = 'chats-item';
    chatItem.setAttribute('data-id', friend.id);
    chatItem.setAttribute('data-name', friend.name);
    chatItem.onclick = () => {
      if (this.router) {
        this.router.navigate(`/live_chat/chat_room?recipient=${friend.name}`);
      } else {
        console.warn('Router instance is undefined');
        return;
      }
    };
    const chatImg = document.createElement('img');
    chatImg.src = friend.profile_picture_url;
    chatImg.alt = friend.name;
    chatImg.className = 'friends-avatar';

    const chatInfo = document.createElement('div');
    chatInfo.className = 'friends-info';

    const chatName = document.createElement('div');
    chatName.className = 'friends-name';
    chatName.textContent = friend.name;

    const messagePreview = document.createElement('div');
    messagePreview.className = 'message-preview';
    messagePreview.textContent = 'Loading...';

    chatInfo.appendChild(chatName);
    chatInfo.appendChild(messagePreview);

    chatItem.appendChild(chatImg);
    chatItem.appendChild(chatInfo);
    return chatItem;
  }
  
  displayChatsList(friends) {
    const friendsListElement = document.querySelector('.friends-scroll-container');
    if (!friendsListElement) {
      console.warn('Friend list container not found');
      return;
    }
    const chatsListElement = document.querySelector('.chats-scroll-container');
    if (!chatsListElement) {
      console.warn('Chat list container not found');
      return;
    }
    friendsListElement.innerHTML = '';
    chatsListElement.innerHTML = '';
  
    if (friends.length === 0) {
      const noFriendsMessage = document.createElement('div');
      noFriendsMessage.className = 'no-friends-message';
      noFriendsMessage.textContent = 'No friends available';
      friendsListElement.appendChild(noFriendsMessage);
    }
    friends.forEach((friend) => {
      if (friend.chat) {
        chatsListElement.appendChild(this.createChatItem(friend));
      }
      const friendItem = document.createElement('div');
      const buttons = [];
      if (friend.status === 'BF') {
        friendItem.className = 'friends-item friends';
        buttons = this.createFriendsFilterButtons(friend);
      } else if (friend.status === 'BL') {
        friendItem.className = 'friends-item blocked';
        buttons = this.createBlockedFilterButtons(friend);
      }
      friendItem.setAttribute('data-id', friend.id);
      friendItem.setAttribute('data-name', friend.name);
  
      const friendImg = document.createElement('img');
      friendImg.src = friend.profile_picture_url;
      friendImg.alt = friend.name;
      friendImg.className = 'friends-avatar';
  
      const friendInfo = document.createElement('div');
      friendInfo.className = 'friends-info';
  
      const friendName = document.createElement('div');
      friendName.className = 'friends-name';
      friendName.textContent = friend.name;
    
      friendInfo.appendChild(friendName);
      friendItem.appendChild(friendImg);
      friendItem.appendChild(friendInfo);
      buttons.forEach(button => friendItem.appendChild(button));
      friendsListElement.appendChild(friendItem);
    });
    
    if (document.querySelector('.chats-scroll-container').children.length === 0) {
      const noChatsMessage = document.createElement('div');
      noChatsMessage.className = 'no-chats-message';
      noChatsMessage.textContent = 'No chats available';
      document.querySelector('.chats-scroll-container').appendChild(noChatsMessage);
    }
    this.ws.send(JSON.stringify({
      'type': 'message_preview',
      'context': 'home'
    }));
    this.applyFilter();
  }

  createFriendsFilterButtons(friend) {
    console.log('Friend:', friend);
    const chatButton = document.createElement('button');
    chatButton.id = 'chat-button';
    chatButton.onclick = () => {
      this.router.navigate(`/live_chat/chat_room?recipient=${friend.name}`);
    };
  
    const svgContent = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="100%" height="100%" fill="#149a00" stroke="#149a00" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" style="transform: translate(0, 6px);">
        <!-- Border with offset -->
        <path class="border" d="M25 20a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h5l2 2 2-2h11z"
              fill="none" stroke="#1f7112" stroke-width="2"
              transform="translate(0, 1)"/>
  
        <!-- Chat bubble -->
        <path class="bubble" d="M25 20a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h5l2 2 2-2h11z"/>
  
        <!-- Chat bubble text -->
        <text class="bubble" x="15" y="12.5" font-size="8" text-anchor="middle" fill="white" stroke="none" font-weight="600" dy=".3em">Chat</text>
      </svg>
    `;
  
    chatButton.innerHTML = svgContent;
  
    const blockButton = document.createElement('button');
    blockButton.className = 'mainButton reject';
    blockButton.textContent = 'Block';
    blockButton.onclick = () => {
      this.blockFriend(this.senderId, friend.id);
    };
  
    return [chatButton, blockButton];
  }

  createBlockedFilterButtons(friend) {
    const unblockButton = document.createElement('button');

    if (unblockButton) {
      unblockButton.className = 'mainButton.blocked';
      unblockButton.onclick = () => {
        this.unblockFriend(senderId, receiverId);
      };
    }
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
    
    console.log('Requesting chat history for:', friendId, this.senderId);
    this.sendChatHistoryRequest(this.senderId, friendId);

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

  displayChatMessage(message, type) {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
      const messageItem = document.createElement('div');
      messageItem.className = `chat-message ${type}`;
  
      const messageText = document.createElement('span');
      messageText.className = 'message-text';
      messageText.textContent = `${message.message}`;
  
      const messageTimestamp = document.createElement('span');
      messageTimestamp.className = 'message-timestamp';
      messageTimestamp.textContent = ` (${new Date(message.timestamp).toLocaleTimeString()})`;
  
      messageItem.appendChild(messageText);
      messageItem.appendChild(messageTimestamp);
  
      chatMessages.appendChild(messageItem);
  
      const chatMessagesWrapper = document.querySelector('.chat-messages-wrapper');
      chatMessagesWrapper.scrollTop = chatMessagesWrapper.scrollHeight;
    } else {
      console.warn('Chat messages container not found');
    }
  }
  

  displayChatHistory(messages) {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.innerHTML = '';
        messages.forEach((message) => {
            message.sender_id === this.senderId ? this.displayChatMessage(message, 'sent') : this.displayChatMessage(message, 'received');
        });
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
        if (event.ctrlKey) {
          return;
        }

        if (event.deltaY !== 0) {
          container.scrollLeft += event.deltaY;
          event.preventDefault();
        }
      });
    } else {
      console.warn('User list container not found');
    }
  }

  initFiltering() {
    const btnContainer = document.querySelector('.btn-group');
    const btns = btnContainer.querySelectorAll('.btn-check');
  
    console.log('Filter buttons:', btns);
  
    btns.forEach(btn => {
      btn.addEventListener("click", () => {
        btns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.currentFilter = btn.getAttribute('data-filter') || 'all';
        this.applyFilter();
      });
    });
  
    // Apply initial filter
    this.applyFilter();
  }

  applyFilter() {
    const items = document.getElementsByClassName("friends-item");
    const filter = this.currentFilter === 'all' ? '' : this.currentFilter;
    
    Array.from(items).forEach(item => {
      if (!filter || item.classList.contains(filter)) {
        item.classList.add("show");
      } else {
        item.classList.remove("show");
      }
    });
  }
}


const instance = new ChatHandler();
export default {
  getInstance() {
    return instance;
  }
};

