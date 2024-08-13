import ChatHandler from './chatHandler.js';

class Router {
  constructor(routes) {
    this.routes = routes;
    this.currentRoute = null;
    this.app = null;

    window.addEventListener('popstate', this.handlePopState.bind(this));
    this.bindLinks();
  }

  init(app) {
    this.app = app;
    this.navigate(window.location.pathname, false); // Don't push state on initial load
  }

  addRoute(path, templateUrl) {
    this.routes.push({ path, templateUrl });
  }

  async navigate(path, pushState = true, state = {}) {
    const route = this.matchRoute(path);
    if (route) {
      this.currentRoute = route;
      if (pushState) {
        history.pushState({ path, ...state }, '', path);
      }
      await this.updateView(route.params);
    } else {
      this.handleNotFound(pushState);
    }
  
    if (this.onNavigate) {
      this.onNavigate(route.params);
    }
  }  

  matchRoute(path) {
    for (const route of this.routes) {
      const paramNames = [];
      const regexPath = route.path.replace(/:(\w+)/g, (_, key) => {
        paramNames.push(key);
        return '([^\\/]+)';
      });
      const regex = new RegExp(`^${regexPath}$`);
      const match = path.match(regex);
      if (match) {
        const params = paramNames.reduce((acc, paramName, index) => {
          acc[paramName] = match[index + 1];
          return acc;
        }, {});
        return { ...route, params };
      }
    }
    return null;
  }

  async updateView(params = {}) {
    if (this.app && this.currentRoute) {
      try {
        const response = await fetch(this.currentRoute.templateUrl);
        const html = await response.text();
        this.app.innerHTML = this.extractContent(html);

        this.onViewUpdated(params);
      } catch (error) {
        console.error('Error loading template:', error);
        this.app.innerHTML = '<p>Error loading content</p>';
      }
    }
  }

  extractContent(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const content = doc.getElementById('content');
    return content ? content.innerHTML : '<p>No content found</p>';
  }

  handleNotFound(pushState) {
    this.currentRoute = this.routes.find(route => route.path === "/404");
    if (pushState) {
      history.pushState(null, '', "/404");
    }
    this.updateView();
  }

  handlePopState(event) {
    const path = window.location.pathname;
    const state = event.state || {};
    this.navigate(path, false, state);
  }

  bindLinks() {
    document.body.addEventListener('click', (event) => {
      if (event.target.tagName === 'A') {
        const href = event.target.getAttribute('href');
        if (href.startsWith('/')) {
          event.preventDefault();
          this.navigate(href);
        }
      }
    });
  }

  onViewUpdated(params) {
    if (window.location.pathname.startsWith('/live_chat')) {
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
  }
}

export default Router;
