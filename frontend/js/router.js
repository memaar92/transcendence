import { updateChat } from "./live-chat.js";
import { api } from "./api.js";
import { hubSocket, showAlert } from "./app.js";
//import { chat_handler } from "./chatHandler.js";

class Router {
  constructor(routes) {
    this.routes = routes;
    this.currentRoute = null;
    this.app = null;
    this.currentHistoryPosition = 0;
    this.maxHistoryPosition = 0;
    this.excludedPaths = ['/game'];
    this.unregistered_urls = ["/", "/home", "/login", "/register", "/email_verification"];
    console.log("Router: constructor called");

    api.get("/token/check/").then(
      async (result) => {
        const json = await result.json();
        var status = json["logged-in"];

        if (!status) {
            const formData = new FormData();
            formData.append("refresh", "");
      
            const result = await api.post_multipart("/token/refresh/", formData);
            if (result.status != 200) {
                if (this.unregistered_urls.includes(window.location.pathname)) {
                    window.addEventListener("popstate", this.handlePopState.bind(this));
                    this.bindLinks();
                    this.navigate(window.location.pathname + window.location.search, false);
                  } else {
                      console.log("Auth token and refresh token expired: caught by router.js");
                      const params = new URLSearchParams(window.location.search);
                      if (window.location.pathname == "/42auth_failed" && params.has("error")) {
                          const error = params.get("error");
                          if (error == "42email") {
                              showAlert("This email has already been used for standard login")
                          } else {
                              showAlert("An error occurred when signing in with 42")
                          }
                      } else {
                        const logged_out = document.getElementById("logged_out");
                        let bsAlert = new bootstrap.Toast(logged_out);
                        bsAlert.show();
                      }
                      await this.navigate('/home');
                      return;
                }
            } else {
                status = true;
            }
        }

        if (status) {
          hubSocket.connect();
        }

        //if (!status && !this.unregistered_urls.includes(window.location.pathname)) {
        //    this.navigate("/home");
        //    return;
        //}

        if (status && this.unregistered_urls.includes(window.location.pathname)) {
          this.navigate("/main_menu");
        } else {
          window.addEventListener("popstate", this.handlePopState.bind(this));
          this.bindLinks();
          this.navigate(window.location.pathname + window.location.search, false);
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

  matchRoute(path) {
    const [pathWithoutQuery, queryString] = path.split('?');
  
    for (const route of this.routes) {
      const paramNames = [];
      const regexPath = route.path.replace(/:(\w+)/g, (_, key) => {
        paramNames.push(key);
        return '([^\\/]+)';
      });
      const regex = new RegExp(`^${regexPath}$`);
      const match = pathWithoutQuery.match(regex);
  
      if (match) {
        const params = paramNames.reduce((acc, paramName, index) => {
          acc[paramName] = match[index + 1];
          return acc;
        }, {});
  
        if (queryString) {
          const queryParams = new URLSearchParams(queryString);
          queryParams.forEach((value, key) => {
            params[key] = value;
          });
        }
  
        return { ...route, params };
      }
    }
    return null;
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
    if (!route) {
      route = this.matchRoute(path);
    }

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

    this.currentRoute = route;

    if (pushState && oldPath !== path) {
      history.pushState({ path: path }, "", path);
    }
    await this.updateView();
  }

  handlePopState(event) {
    if (event.state && event.state.path) {
      this.navigate(event.state.path, false);
    } else {
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

  handlePostUpdate() {
    updateChat(this, this.currentRoute.params);
    //chat_handler.updateChat(this, this.currentRoute.params);
  }

  insertNotification() {
    const notificationDiv = document.createElement('div');
    notificationDiv.setAttribute('id', 'notifications');
    notificationDiv.setAttribute('position', 'fixed');
    notificationDiv.style.cssText = 'position:fixed;top:0;width:100%;padding:10px;text-align:center;z-index:1000;';
    this.app.prepend(notificationDiv);
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

      if (!this.excludedPaths.includes(this.currentRoute.path)) {
        this.insertNotification();
      }

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
    if (!this.unregistered_urls.includes(this.currentRoute.path)) {
      this.handlePostUpdate();
    }
  }
}

export default Router;
