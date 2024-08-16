import { router } from "./app.js";
const API_BASE_URL = "api";

export const api = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (response.status == 401)
    {
      const json = await response.json()
      if (json["code"] == "token_not_valid")
      {
        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
          method : "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: "{\"refresh\" : \"hello\"}"
        });
        const json = await response.json()
        if (json["code"] == "token_not_valid")
          router.navigate("/home");
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
