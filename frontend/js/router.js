import { api } from "./api.js";
import { hubSocket } from "./app.js";

class Router {
  constructor(routes) {
    this.routes = routes;
    this.currentRoute = null;
    this.app = null;
    this.currentHistoryPosition = 0;
    this.maxHistoryPosition = 0;

    api.get("/token/check/").then(
      async (result) => {
        var unregistered_urls = new Set(["/", "/home", "/login", "/register", "/email_verification"]);

        const json = await result.json()
        const status = json["logged-in"]
        if (!status && !unregistered_urls.has(window.location.pathname))
        {
          this.navigate("/home");
          return;
        }
        if (status){
          hubSocket.connect();
        }

        if (status && unregistered_urls.has(window.location.pathname)) {
          this.navigate("/main_menu");
        } else {
          window.addEventListener("popstate", this.handlePopState.bind(this));
          this.bindLinks();
          this.navigate(window.location.pathname);
        }
      }
    );
  }

  init(app) {
    this.app = app;
  }

  addRoute(path, templateUrl) {
    this.routes.push({ path, templateUrl });
  }

  async navigate(path, pushState = true) {
    const oldPath = this.currentRoute ? this.currentRoute.path : null;
    // console.log(oldPath, this.currentRoute.path)
    if (this.currentRoute && oldPath == path)
    {
      return;
    }
  
    // Find the new route
    let route = this.routes.find((r) => r.path === path);
  
    // Handle special cases
    if (path.startsWith("/users/")) {
      route = {
        templateUrl: "/routes/users.html",
        path: "User"
      };
      localStorage.setItem("UID", path.substr(7));
    } else if (!route) {
      route = {
        path: "/404",
        templateUrl: "/routes/404.html"
      };
    }
  
    // Update current route
    this.currentRoute = route;
  
    // Push state if needed
    if (pushState && oldPath !== path) {
      history.pushState({ path: path }, "", path);
    }
  
    await this.updateView();
  }
  
  handlePopState(event) {


  
    if (event.state && event.state.path) {

      // Use navigate but don't push a new state
      this.navigate(event.state.path, false);
    } else {
      // Handle the case when there's no state (e.g., initial page load)

      this.navigate(window.location.pathname, false);
    }
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
