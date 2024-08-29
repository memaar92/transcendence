import { router } from "./app.js";
const API_BASE_URL = "api";

export const api = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (response.status == 401) // Not Authorized
    {
      const json = await response.json()
      if (json["detail"] == "Authentication credentials were not provided.")
      {
          // No token
          const logged_out = document.getElementById('logged_out');
          let bsAlert = new bootstrap.Toast(logged_out);
          bsAlert.show();
          await router.navigate("/home");
      }
      if (json["code"] == "token_not_valid")
      {
        // refresh token expired
        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
          method : "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: "{\"refresh\" : \"hello\"}"
        });
        const json = await response.json()
        if (json["code"] == "token_not_valid")
        {
          // access token expired
          const logged_out = document.getElementById('logged_out');
          let bsAlert = new bootstrap.Toast(logged_out);
          bsAlert.show();
          await router.navigate("/home");
        }
        return await fetch(`${API_BASE_URL}${endpoint}`);
      }
    }
    return response;
  },

  post: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    return response;
  },

  delete: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
    });
    return response;
  },
};
