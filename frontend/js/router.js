import { handleButtonClick } from './loginHandlers.js'
class Router {
    constructor(routes) {
      this.routes = routes;
      this.currentRoute = null;
      this.app = null;
      this.currentHistoryPosition = 0;
      this.maxHistoryPosition = 0;

      // TODO login check
  
      window.addEventListener('popstate', this.handlePopState.bind(this));
      this.bindLinks();
    }
  
    init(app) {
      this.app = app;
      this.navigate(window.location.pathname);
    }
  
    addRoute(path, templateUrl) {
      this.routes.push({ path, templateUrl });
    }
  
    async navigate(path, pushState = true) {
        const route = this.routes.find(route => route.path === path);
        if (route) {
            this.currentRoute = route;
            if (pushState) {
                this.currentHistoryPosition++;
                this.maxHistoryPosition = this.currentHistoryPosition;
                const title_temp = document.title;
                document.title = route.path.slice(1).replace('_', "-");
                history.pushState({ position: this.currentHistoryPosition }, '', path);
                document.title = title_temp;
            }
            await this.updateView();
        }
        else
        {
          this.currentRoute = this.routes.find(route => route.path === "/404");
            if (pushState) {
                this.currentHistoryPosition++;
                this.maxHistoryPosition = this.currentHistoryPosition;
                history.pushState({ position: this.currentHistoryPosition }, '', "/404");
            }
            await this.updateView();
        }
        if (this.onNavigate) {
            this.onNavigate();
          }
      
    }

        handlePopState(event) {
            if (event.state && event.state.position) {
                if (event.state.position < this.currentHistoryPosition) {
                    this.currentHistoryPosition--;
                } else {
                    this.currentHistoryPosition++;
                }
            }
            this.navigate(window.location.pathname, false);
        }

        bindLinks() {
            document.addEventListener('click', (e) => {
                if (e.target.matches('[data-router-link]')) {
                    e.preventDefault();
                    const path = e.target.getAttribute('href');
                    this.navigate(path);
                }
            });
        }

        async updateView() {
            if (this.app && this.currentRoute) {
              try {
                const response = await fetch(this.currentRoute.templateUrl);
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const content = doc.getElementById('content');
                if (content) {
                  this.app.innerHTML = content.innerHTML;
                } else {
                  console.error('No content div found in the loaded HTML');
                }
                const buttons = document.querySelectorAll('button');
                buttons.forEach(button => {
                  button.addEventListener('click', handleButtonClick);
                });
              } catch (error) {
                console.error('Error loading template:', error);
                this.app.innerHTML = '<p>Error loading content</p>';
              }
            }
          }
}
  
export default Router;
  