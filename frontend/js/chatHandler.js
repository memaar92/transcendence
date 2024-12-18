import { api } from './api.js';
import { createProfileButton } from './utility/createProfileButton.js';

const API_BASE_URL = `${window.location.origin}/api`;

class ChatHandler {
  constructor() {
    this.ws = null;
    this.senderId = null;
    this.currentReceiverId = null;
    this.onlineUserIds = [];
    this.router = null;
    this.context = null;
    this.currentFilter = 'all';
    this.boundSearchInputHandler = this.searchInputHandler.bind(this);
  }
  
  async initChatSocket(context) {

    const url = `wss://${window.location.host}/ws/live_chat/}`;

    console.log('Creating new WebSocket connection');
    console.log('Checking token');
    const auth = await this.checkToken();
    if (!auth) {
        await this.refreshToken();
    }
    
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      // console.log('WebSocket connection opened in context:', context);
    };
    
    this.ws.onmessage = this.onMessage.bind(this);
    this.ws.onclose = (e) => this.onClose(e, context);
    
    }

  async initContext(params, router, context) {
    this.router = router;
    this.context = context;
    // console.log('Initializing context:', context);
  
    if (this.ws.readyState === WebSocket.CONNECTING) {
        await new Promise((resolve) => {
            this.ws.onopen = () => resolve();
        });
    }
  
    this.ws.send(JSON.stringify({ "type": context, "context": 'setup' }));
  
    switch (context) {
        case 'chat':
            this.currentReceiverId = params.recipient;
            this.chatWindowOpened = false;
            break;
        case 'home':
            this.currentReceiverId = null;
            this.initFiltering();
            this.initTabHandling();
            document.getElementById("back").addEventListener("click", async (e) => {
                router.navigate("/main_menu");
            });
            const searchInput = document.getElementById('search-input');
            searchInput.removeEventListener('keydown', this.boundSearchInputHandler);
            searchInput.addEventListener('keydown', this.boundSearchInputHandler);
            break;
        default:
            this.currentReceiverId = null;
            break;
    }
  }
      
  async getUserIdfromName(name) {
    if (!name) {
      // console.error('Name parameter is required');
      return null;
    }
  
    try {
      const response = await api.get(`/displayname/${name}/`);
      if (response.ok) {
        const json = await response.json();
        return json.user_id || null;
      } else {
        // console.error(`Error fetching user ID: ${response.statusText}`);
        return null;
      }
    } catch (error) {
      // console.error('Error fetching user ID:', error);
      return null;
    }
  }
  
  async checkToken() {
      const response = await api.get('/token/check/');
      const json = await response.json();
      if (json['logged-in'] === false) {
        return false;
      }
      return true;
  }
  
  async refreshToken() {
      const formData = new FormData();
      formData.append("refresh", "");

      const result = await api.post_multipart("/token/refresh/", formData);
      if (result.status != 200) {
          // console.log("Auth token and refresh token expired. Caught by chat socket");
          const logged_out = document.getElementById("logged_out");
          let bsAlert = new bootstrap.Toast(logged_out);
          bsAlert.show();
          await this.router.navigate('/home');
      }
  }

  async onClose(event) {
    // console.log('WebSocket connection closed:', event.code, event.reason);
  }
  
  onMessage(event) {
    const content = JSON.parse(event.data);
    // console.log('Received message:', content);
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
      case 'none':
        this.handleNoneContext(content);
        break;
      default:
        // // console.error('Unknown context:', content.context);
        break;
      }
    }
    
  handleHomeContext(content) {
    // console.log('Handling home context:', content.type);
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
        this.displayNotification("You have a new message from: " + content.sender_name + "!");
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
            // console.warn('Friend not found for sender ID:', content.sender_id);
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
            // console.log('No messages');
            const messagePreview = chatItem.querySelector('.message-preview');
            if (messagePreview) {
              messagePreview.textContent = 'No messages';
            }
          }
        });
        break;
      case 'pending_requests':
        if (content.requests.length > 0)
          this.displayNotification("You have pending friend requests. Check your friends list!");
        this.displayChatRequest(content.requests);
        break;
      case 'game_invite':
        this.displayModal(content, 'Game Invite');
        var friendItem = document.querySelector(`.friends-item[data-id="${content.sender_id}"]`);
        if (friendItem) {
          const existingButton = friendItem.querySelector('#game-invite-button');
          const newGameInviteButton = this.createGameButton(content.sender_id, content.receiver_id);

          if (existingButton) {
            friendItem.replaceChild(newGameInviteButton, existingButton);
          } else {
            // console.warn('Existing game invite button not found');
            friendItem.appendChild(newGameInviteButton);
        }
        } else {
            // console.warn('Friend item not found');
        }
        break;
      case 'match_id':
        if (content.match_id) {
          window.localStorage.setItem('game_id', content.match_id);
          this.router.navigate('/game');
        }
        break;
      case 'game_invite_cancelled':
        var friendItem = document.querySelector(`.friends-item[data-id="${content.message}"]`);
        if (friendItem) {
            const existingButton = friendItem.querySelector('#game-invite-button');
            
            const newGameInviteButton = this.createGameButton(null, content.message);
            
            if (existingButton) {
                friendItem.replaceChild(newGameInviteButton, existingButton);
            } else {
                // console.warn('Existing game invite button not found');
                friendItem.appendChild(newGameInviteButton);
            }
        } else {
            // console.warn('Friend item not found');
        }
        break;
      case 'game_error':
        this.displayModal(content, 'Server Message:');
        var friendItem = document.querySelector(`.friends-item[data-id="${content.misc}"]`);
        if (friendItem) {
            const existingButton = friendItem.querySelector('#game-invite-button');
            
            var newGameInviteButton = this.createGameButton(null, content.misc);
            if (content.flag === true) {
                newGameInviteButton = this.createGameButton(content.misc, content.sender_id);
            }
            
            if (existingButton) {
                friendItem.replaceChild(newGameInviteButton, existingButton);
            } else {
                // console.warn('Existing game invite button not found');
                friendItem.appendChild(newGameInviteButton);
            }
        } else {
            // console.warn('Friend item not found');
        }
        break;
      case 'tournament':
        this.displayNotification(content.message);
        break;
      default:
        // console.error('Unknown context:', content.type);
        break;
      }
    }
        
  handleChatContext(content) {
    // console.log('Handling chat context:', content.type);
    switch (content.type) {
      case 'user_list':
        const parsedData = JSON.parse(content.users);
        const users = parsedData.users;
        const indicator = document.getElementById('status-indicator');
        let userFound = false;
    
        users.forEach((user) => {
          if (user.name === this.currentReceiverId) {
            userFound = true;
            if (indicator) {
              indicator.classList.add('online');
            }
          }
        });
    
        if (!userFound && indicator) {
          indicator.classList.remove('online');
        }
        break;
      case 'chat_message':
        if (content.sender_name !== this.currentReceiverId) {
          this.displayNotification("You have a new message from: " + content.sender_name + "!");
        }
        if (content.sender_name === this.currentReceiverId) {
          this.displayChatMessage(content, 'received');
        }
        break;
      case 'tournament':
        this.displayNotification(content.message);
        break;
      case 'game_invite':
        this.displayNotification("You have a new game invite from: " + content.sender_name + "!");
        break;
      case 'chat_history':
        if (this.chatHistoryResolve) {
            this.chatHistoryResolve(content.messages);
            this.chatHistoryResolve = null;
        }
        this.displayChatHistory(content.messages);
        break;
      case 'error':
        this.displaySystemMessage(content.message);
        break;
      case 'match_id':
        if (content.match_id) {
          window.localStorage.setItem('game_id', content.match_id);
          this.router.navigate('/game');
        }
        break;
      default:
        // console.error('Error:', content.type);
        break;
    }
  }

  handleNoneContext(content) {
    // console.log('Handling none context:', content.type);
    switch (content.type) {
      case 'chat_message':
        this.displayIndicator();
        this.displayNotification("You have a new message from: " + content.sender_name + "!");
        break;
      case 'game_invite':
        this.displayNotification("You have a new game invite from: " + content.sender_name + "!");
        break;
      case 'pending_requests':
        this.displayNotification("You have pending friend requests. Check your friends list!");
        if (window.location.pathname.startsWith('/users/')) {
          this.updateProfileButtons();
        }
        break;
      case 'unread_counts':
        if (Object.keys(content.unread_messages).length > 0) {
          this.displayIndicator();
        }
        break;
      case 'match_id':
        if (content.match_id) {
          window.localStorage.setItem('game_id', content.match_id);
          this.router.navigate('/game');
        }
        break;
      case 'tournament':
        this.displayNotification(content.message);
        break;
      case 'friends_list':
        if (window.location.pathname.startsWith('/users/')) {
          this.updateProfileButtons();
        }
        break;
      default:
        break;
    }
  }

  async updateProfileButtons() {
    await createProfileButton();
  }

  displayIndicator() {
    if (window.location.pathname !== '/main_menu')
      return;
    const chatMenuItem = document.getElementById('chat-menu-item');
    if (!chatMenuItem) {
      // console.warn('Chat menu item not found');
      return;
    }
  
    const chatLink = chatMenuItem.querySelector('a');
    if (!chatLink) {
      // console.warn('Chat link not found');
      return;
    }

    let indicator = document.getElementById('chat-notification-indicator');
    if (!indicator) {
      indicator = document.createElement('span');
      indicator.id = 'chat-notification-indicator';
      indicator.classList.add('chat-notification-indicator');
      chatLink.appendChild(indicator);
    }
    
    indicator.classList.add('pulse-animation');
    setTimeout(() => {
      indicator.classList.remove('pulse-animation');
    },
    3000);
  }

  displayNotification(message) {
    const container = document.getElementById('notifications');
    if (!container) {
      return;
    }
    const toastEl = document.createElement('div');
    toastEl.classList.add('chat-toast', 'notification');
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.setAttribute('data-bs-delay', '5000');

    toastEl.innerHTML = `
      <div class="toast-header chat-toast-header">
        <strong class="me-auto">Notification</strong>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body chat-toast-body">
        ${message}
      </div>
    `;

    container.appendChild(toastEl);

    const toast = new bootstrap.Toast(toastEl);
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => {
      setTimeout(() => {
        toastEl.remove();
      }, 300);
    });
  }

  createGameButton(inviter_id, friend_id) {
    const gameInviteButton = document.createElement('button');
    gameInviteButton.className = 'button';
    gameInviteButton.id = 'game-invite-button';
  
    let buttonState = 0;
  
    const updateButtonState = () => {
      gameInviteButton.removeEventListener('click', sendInvite);
      gameInviteButton.removeEventListener('click', cancelInvite);
      gameInviteButton.removeEventListener('click', sendAcceptance);
      
      if (buttonState === 0) {
        gameInviteButton.textContent = 'Cancel';
        gameInviteButton.addEventListener('click', cancelInvite);
      } else if (buttonState === 1) {
        gameInviteButton.textContent = 'Play';
        gameInviteButton.addEventListener('click', sendInvite, { once: true });
      } else {
        gameInviteButton.textContent = 'Join';
        gameInviteButton.addEventListener('click', sendAcceptance);
      }
    };
    
    const sendInvite = () => {
      gameInviteButton.disabled = true;
      this.ws.send(JSON.stringify({
        'type': 'game_invite',
        'sender_id': this.senderId,
        'receiver_id': friend_id
      }));
      buttonState = 0;
      gameInviteButton.disabled = false;
      updateButtonState();
    };
    
    const cancelInvite = () => {
      this.ws.send(JSON.stringify({
        'type': 'game_invite_cancelled',
        'sender_id': this.senderId,
        'receiver_id': friend_id
      }));
      buttonState = 1;
      updateButtonState();
    };

    const sendAcceptance = () => {
        this.ws.send(JSON.stringify({
          'type': 'game_invite_accepted',
          'sender_id': inviter_id,
          'receiver_id': this.senderId
        }));
        buttonState = 1;
        updateButtonState();
    };

    if (inviter_id === null) {
      buttonState = 1;
      // console.log('Inviter ID is null');
      updateButtonState();
    } else if (inviter_id === this.senderId) {
      buttonState = 0;
      // console.log('Inviter ID is sender ID');
      updateButtonState();
    } else {
      buttonState = 2;
      // console.log('Inviter ID is not sender ID');
      updateButtonState();
    }

    return gameInviteButton;
  }
        
  showLatestMessage(message, senderId, friendId) {
    if (document.querySelector('.no-chats-message')) {
      document.querySelector('.no-chats-message').remove();
    }
    const chatItem = document.querySelector(`.chats-item[data-id="${friendId}"]`);
    if (chatItem) {
      const messagePreview = chatItem.querySelector('.message-preview');
      if (messagePreview && message) {
        if (message.length > 30) {
          message = message.slice(0, 30) + '...';
        }
        if (senderId === this.senderId) {
          messagePreview.textContent = `You: ${message}`;
        } else {
          messagePreview.textContent = message;
        }
      } else {
        // console.log('preview not found');
      }
    }
  }

  displayModal(content, msg = null) {
    const modalContainer = document.createElement('div');
    modalContainer.className = 'modal fade';

    const usernameMatch = content.message.match(/(\b\w+\b)$/);
    const username = usernameMatch ? usernameMatch[0] : 'User';
    var message;
    var headerText;
    if (content.type === 'request_status') {
      message = content.message.replace(username, `<span style="color: #0083e8;">${username}</span>`);
      headerText = content.flag ? 'Friend Request Accepted!' : 'Friend Request Denied!';
    } else if (content.type === 'game_invite' || content.type === 'game_error') {
      message = content.message;
      headerText = msg;
    }

    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${headerText}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            ${message} ...
          </div>
        </div>
      </div>
    `;

    document.body.prepend(modalContainer);

    let modalInstance;
    try {
      modalInstance = new bootstrap.Modal(modalContainer, {
        keyboard: true,
        backdrop: 'static'
      });
      modalInstance.show();
    } catch (error) {
      // console.error('Error initializing modal:', error);
      modalContainer.remove();
      return;
    }

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        modalInstance.hide();
      }
    };

    document.addEventListener('keydown', handleEscapeKey);

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
      // console.warn('Message, receiver ID is empty, or sender and receiver are the same');
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
      // console.warn('Friend item not found (unread messages):', senderId);
    }
  }

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
      button.className = 'button reject';
    else 
      button.className = 'button';
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

      // Remove the game button
      const gameButton = friendItem.querySelector('#game-invite-button');
      if (gameButton) {
        gameButton.remove();
      }
  
      // Update the block button to unblock button
      const blockButton = friendItem.querySelector('.button.reject');
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
  }

  displayUserList(data) {
    const parsedData = JSON.parse(data);
    const users = parsedData.users;
    const userListContainer = document.getElementById('user-list-container');
    if (!userListContainer) {
      // console.warn('User list container not found');
      return;
    }
    const userListWrapper = userListContainer.querySelector('.user-list-wrapper');
    
    if (!userListWrapper) {
      // console.warn('User list wrapper not found');
      return;
    }
    
    this.onlineUserIds = users.map(user => user.id);
    userListWrapper.innerHTML = '';
  

    users.forEach((user) => {
      const userItem = document.createElement('div');
      userItem.className = 'user-item';
  
      const userImg = document.createElement('img');
      userImg.src = user.profile_picture_url;
      userImg.onclick = () => {
        this.router.navigate(`/users/${user.id}`);
      };
      userImg.alt = user.name;
      userImg.className = 'user-avatar';
  
      const userName = document.createElement('div');
      userName.className = 'username';
      userName.textContent = user.name;
  
      userItem.appendChild(userImg);
      userItem.appendChild(userName);
  
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
        // console.warn('Image not found for chat item:', friendId);
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
          // console.warn('Image not found for friend item:', friendId);
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
        // console.warn('Router instance is undefined');
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
      // console.warn('Friend list container not found');
      return;
    }
    const chatsListElement = document.querySelector('.chats-scroll-container');
    if (!chatsListElement) {
      // console.warn('Chat list container not found');
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
      if (friend.status === 'PD') {
        return;
      }
      if (friend.chat) {
        chatsListElement.appendChild(this.createChatItem(friend));
      }
      const friendItem = document.createElement('div');
      buttons = [];
      if (friend.status === 'BF') {
        friendItem.className = 'friends-item friends';
        var buttons = this.createFriendsFilterButtons(friend);
      } else if (friend.status === 'BL') {
        if (friend.blocker_id === this.senderId) {
          friendItem.className = 'friends-item blocked';
          buttons = this.createBlockedFilterButtons(friend);
        } else
          friendItem.className = 'friends-item friends';
      }
      friendItem.setAttribute('data-id', friend.id);
      friendItem.setAttribute('data-name', friend.name);
  
      const friendImg = document.createElement('img');
      friendImg.src = friend.profile_picture_url;
      friendImg.onclick = () => {
        this.router.navigate(`/users/${friend.id}`);
      };
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
    const chatButton = document.createElement('button');
    chatButton.id = 'chat-button';
    // console.log("Opening chat with: ", friend.name);
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
    blockButton.className = 'button reject';
    blockButton.textContent = 'Block';
    blockButton.onclick = () => {
      this.blockFriend(this.senderId, friend.id);
    };
    const gameButton = this.createGameButton(friend.inviter_id, friend.id);

    return [gameButton, chatButton, blockButton];
  }

  createBlockedFilterButtons(friend) {
    const unblockButton = document.createElement('button');

    if (unblockButton) {
      unblockButton.className = 'button';
      unblockButton.textContent = 'Unblock';
      unblockButton.onclick = () => {
        this.unblockFriend(this.senderId, friend.id);
      };
    }
    return [unblockButton];
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
  
    // console.log('Opening chat window with friend ID:', friendId);
    chatTitle.textContent = `Chat with ${friendId}`;
    chatWindow.classList.add('open');
  
    // messagesContainer.innerHTML = '';
    messageInput.value = '';
    this.currentReceiverId = friendId;
    
    this.sendChatHistoryRequest(this.senderId, friendId);

    sendButton.addEventListener('click', () => {
      this.sendMessage(this.currentReceiverId);
    });
    closeButton.addEventListener('click', () => {
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
      messageTimestamp.textContent = ` (${new Date(message.timestamp).toLocaleString()})`;
  
      messageItem.appendChild(messageText);
      messageItem.appendChild(messageTimestamp);
  
      chatMessages.appendChild(messageItem);
  
      const chatMessagesWrapper = document.querySelector('.chat-messages-wrapper');
      chatMessagesWrapper.scrollTop = chatMessagesWrapper.scrollHeight;
    } else {
      // console.warn('Chat messages container not found');
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
        // console.warn('Chat messages container not found');
    }
  }


  displaySystemMessage(message) {
    const messages = document.getElementById('chat-window');
    if (messages) {
      const messageItem = document.createElement('div');
      messageItem.textContent = message;
      messages.appendChild(messageItem);
    } else {
      // console.warn('Chat window not found');
    }
  }

  sendChatHistoryRequest(senderId, receiverId) {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN && senderId && receiverId) {
        this.chatHistoryResolve = resolve;
  
        this.ws.send(JSON.stringify({
          type: 'chat_history',
          sender_id: senderId,
          receiver_id: receiverId,
        }));
  
        setTimeout(() => {
          reject(new Error('Chat history request timed out'));
        }, 5000);
  
      } else {
        reject(new Error('WebSocket is not open or IDs are missing'));
      }
    });
  }
  

  initFiltering() {
    const btnContainer = document.querySelector('.btn-group');
    const btns = btnContainer.querySelectorAll('.btn-check');
  
    if (btns === null)
      return;
  
    btns.forEach(btn => {
      btn.addEventListener("click", () => {
        btns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.currentFilter = btn.getAttribute('data-filter') || 'all';
        this.applyFilter();
      });
    });
  
    this.applyFilter();
  }

  initTabHandling() {
    const tabs = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-pane');

    tabs.forEach(tab => {
        tab.addEventListener('click', (event) => {
            event.preventDefault();

            const targetId = tab.getAttribute('href').substring(1);
            const targetTabContent = document.getElementById(targetId);

            const tabInstance = new bootstrap.Tab(tab);
            
            tabInstance.show();

            localStorage.setItem('activeTab', tab.id);
        });
    });

    const activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
        const activeTabElement = document.getElementById(activeTab);
        const tabInstance = new bootstrap.Tab(activeTabElement);
        tabInstance.show();
    } else {
        const defaultTab = document.querySelector('.nav-link.active');
        const tabInstance = new bootstrap.Tab(defaultTab);
        tabInstance.show();
    }

    tabContents.forEach(tabContent => {
        tabContent.classList.remove('d-none');
    });
  }

  async searchInputHandler(event) {
    if (event.key === 'Enter') {
      const inputValue = event.target.value;
      if (inputValue.length > 0 && inputValue.length <= 20) {
        const user_id = await this.getUserIdfromName(inputValue);
        if (user_id) {
          await this.router.navigate(`/users/${user_id}`);
          return;
        }
      }
      event.target.style.animation = 'jitter 0.5s';
      setTimeout(() => {
        event.target.style.animation = '';
      }, 500);
    }
  }

  applyFilter() {
    const items = document.getElementsByClassName("friends-item");
    const filter = this.currentFilter === 'all' ? '' : this.currentFilter;

    Array.from(items).forEach(item => {
      if (!filter || item.classList.contains(filter)) {
        item.classList.add("chat-show");
      } else {
        item.classList.remove("chat-show");
      }
    });
  }

  async logout() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      console.log('WebSocket connection closed');
    }
    this.senderId = null;
    this.currentReceiverId = null;
    this.onlineUserIds = [];
    this.router = null;
    this.context = null;
    this.currentFilter = 'all';
  }
}

const instance = new ChatHandler();
 export default {
   getInstance() {
     return instance;
   }
};