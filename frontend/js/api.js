import { router } from "./app.js";
const API_BASE_URL = `${window.location.origin}/api`;

const LOGGED_OUT = 0;
const LOGGED_IN = 1;
const MFA_MISSING = 2;

async function handle_not_authorized(response) {
  if (response.status == 403) {
    router.navigate("/verify_2fa");
    return "";
  }
  const json = await response.json();
  console.log(json);
  if (json["detail"] == "Authentication credentials were not provided.") {
    // No token
    const logged_out = document.getElementById("logged_out");
    let bsAlert = new bootstrap.Toast(logged_out);
    bsAlert.show();
    await router.navigate("/home");
    return LOGGED_OUT;
  }
  if (json["code"] == "token_not_valid") {
    // access token expired
    const formData = new FormData();
    formData.append("refresh", "");

    const result = await api.post_multipart("/token/refresh/", formData);
    if (result.status != 200) {
      // access and refresh token expired
      console.log("Auth token and refresh token expired: caught by api.js");
      const logged_out = document.getElementById("logged_out");
      let bsAlert = new bootstrap.Toast(logged_out);
      bsAlert.show();
      await router.navigate("/home");
    } else {
      return LOGGED_IN;
    }
    return LOGGED_OUT;
  }
}

export const api = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok && response.status != 404) {
      // Not Authorized
      if ((await handle_not_authorized(response)) == LOGGED_IN) {
        return await fetch(`${API_BASE_URL}${endpoint}`);
      } else {
        return null;
      }
    }
    if (response.status == 404) {
      await router.navigate("/404");
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
    console.log(response);
    if (!response.ok && response.status != 404) {
      // Not Authorized
      if ((await handle_not_authorized(response)) == LOGGED_IN) {
        return await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });
      } else {
        return null;
      }
    }
    return response;
  },

  post_multipart: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      body: data,
    });
    return response;
  },

  patch: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!response.ok && response.status != 404) {
      // Not Authorized
      if ((await handle_not_authorized(response)) == LOGGED_IN) {
        return await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });
      } else {
        return null;
      }
    }
    return response;
  },

  patch_multipart: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PATCH",
      body: data,
    });
    if (!response.ok && response.status != 404) {
      // Not Authorized
      if ((await handle_not_authorized(response)) == LOGGED_IN) {
        return await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "PATCH",
          body: data,
        });
      } else {
        return null;
      }
    }
    return response;
  },



  delete: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
    });
    if (!response.ok && response.status != 404) {
      // Not Authorized
      if ((await handle_not_authorized(response)) == LOGGED_IN) {
        return await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "DELETE",
        });
      } else {
        return null;
      }
    }
    return response;
  },
};
