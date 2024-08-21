import ChatHandler from './chatHandler.js';

export function updateChat(router, params) {
    console.log('Initializing chat with params:', params);
    const chatHandler = ChatHandler.getInstance();
    if (window.location.pathname === '/live_chat') {
      chatHandler.init(params, router, 'home');
    }
    else if (window.location.pathname === '/live_chat/chat_room') {
      // if (!params.recipient)
      //   router.navigate('/404');
      chatHandler.init(params, router, 'chat');
    }
}
