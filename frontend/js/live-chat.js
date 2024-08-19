import ChatHandler from './chatHandler.js';

export function updateChat(params) {
    console.log('Initializing chat with params:', params);
    const authToken = localStorage.getItem('authToken');
    const chatHandler = ChatHandler.getInstance();
    if (window.location.pathname === '/live_chat') {
      chatHandler.init(authToken, params, this, 'home');
    }
    else if (window.location.pathname === '/live_chat/' + params.username) {
      chatHandler.init(authToken, params, this, 'chat');
    }
}
