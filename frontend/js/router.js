class Router {
  constructor(routes) {
    this.routes = routes;
    this.currentRoute = null;
    this.app = null;
    this.currentHistoryPosition = 0;
    this.maxHistoryPosition = 0;

    // TODO login check

    window.addEventListener("popstate", this.handlePopState.bind(this));
    this.bindLinks();
  }

  init(app) {
    this.app = app;
    this.navigate(window.location.pathname);
  }

  addRoute(path, templateUrl) {
    this.routes.push({ path, templateUrl });
  }

  async navigate(path) {
    const route = this.routes.find((route) => route.path === path);
    this.currentRoute = route;

    if (path.startsWith("/users/")) {
      this.currentRoute = {};
      localStorage.setItem("UID", path.substr(7));
      this.currentRoute.templateUrl = "/routes/users.html";
      this.currentRoute.path = "User";
    } else if (!route) {
      this.currentRoute = {};
      this.currentRoute.path = "/404";
      this.currentRoute.templateUrl = "/routes/404.html";
    }

    this.currentHistoryPosition++;
    this.maxHistoryPosition = this.currentHistoryPosition;
    const title_temp = document.title;
    document.title = this.currentRoute.path;
    history.pushState({ position: this.currentHistoryPosition }, "", path);
    document.title = title_temp;
    await this.updateView();
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
    document.addEventListener("click", (e) => {
      if (e.target.matches("[data-router-link]")) {
        e.preventDefault();
        const path = e.target.getAttribute("href");
        this.navigate(path);
      }
    });
  }

  async updateView() {
    if (!this.app || !this.currentRoute) return;

    try {
      const response = await fetch(this.currentRoute.templateUrl);
      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, "text/html");

      this.app.innerHTML = "";
      document
        .querySelectorAll("script[data-dynamic-script]")
        .forEach((script) => script.remove());

      this.app.append(...doc.body.childNodes);

      const loadScript = (scriptElement) => {
        return new Promise((resolve, reject) => {
          const newScript = document.createElement("script");

          Array.from(scriptElement.attributes).forEach((attr) => {
            newScript.setAttribute(attr.name, attr.value);
          });

          if (newScript.src) {
            newScript.src = `${newScript.src}?v=${Date.now()}`;
          }

          newScript.setAttribute("data-dynamic-script", "true");
          newScript.onload = resolve;
          newScript.onerror = reject;

          document.body.appendChild(newScript);
        });
      };

      const scripts = Array.from(doc.querySelectorAll("script"));
      for (const script of scripts) {
        await loadScript(script);
      }
    } catch (error) {
      this.app.innerHTML = "<p>Error loading content</p>";
    }
  }
}

export default Router;
