import ChatHandler from './chatHandler.js';
//import { chatHandler } from "./app";

export async function updateChat(router, params) {
    console.log('Initializing chat with params:', params);
    const chatHandler = ChatHandler.getInstance();
    if (window.location.pathname === '/live_chat') {
      if (chatHandler.ws === null) {
        await chatHandler.initChatSocket('home');
      }
      await chatHandler.initContext(params, router, 'home');
    }
    else if (window.location.pathname === '/live_chat/chat_room') {
      if (chatHandler.ws === null) {
        await chatHandler.initChatSocket('chat');
      }
      await chatHandler.initContext(params, router, 'chat');
    }
    else {
      if (chatHandler.ws === null) {
        await chatHandler.initChatSocket('none');
      }
      await chatHandler.initContext(params, router, 'none');
    }
}


