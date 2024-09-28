import { router } from "./app.js";
const API_BASE_URL = "https://localhost/api";


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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
        // access token expired
        const formData = new FormData();
        formData.append('refresh', '');  // Add your refresh token or leave it as empty

        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
            method: "POST",
            body: formData  // Use the FormData object as the body
        });
        const json = await response.json()
        if (json["code"] == "token_not_valid")
        {
          // access and refresh token expired
          const logged_out = document.getElementById('logged_out');
          let bsAlert = new bootstrap.Toast(logged_out);
          bsAlert.show();
          await router.navigate("/home");
        }
        return await fetch(`${API_BASE_URL}${endpoint}`);
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
        // access token expired
        const formData = new FormData();
        formData.append('refresh', '');  // Add your refresh token or leave it as empty

        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
            method: "POST",
            body: formData  // Use the FormData object as the body
        });
        const json = await response.json()
        if (json["code"] == "token_not_valid")
        {
          // access and refresh token expired
          const logged_out = document.getElementById('logged_out');
          let bsAlert = new bootstrap.Toast(logged_out);
          bsAlert.show();
          await router.navigate("/home");
        }
        return await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });
      }
    }
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
        // access token expired
        const formData = new FormData();
        formData.append('refresh', '');  // Add your refresh token or leave it as empty

        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
            method: "POST",
            body: formData  // Use the FormData object as the body
        });
        const json = await response.json()
        if (json["code"] == "token_not_valid")
        {
          // access and refresh token expired
          const logged_out = document.getElementById('logged_out');
          let bsAlert = new bootstrap.Toast(logged_out);
          bsAlert.show();
          await router.navigate("/home");
        }
        return await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });
      }
    }
    return response;
  },

  delete: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
    });
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
        // access token expired
        const formData = new FormData();
        formData.append('refresh', '');  // Add your refresh token or leave it as empty

        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
            method: "POST",
            body: formData  // Use the FormData object as the body
        });
        const json = await response.json()
        if (json["code"] == "token_not_valid")
        {
          // access and refresh token expired
          const logged_out = document.getElementById('logged_out');
          let bsAlert = new bootstrap.Toast(logged_out);
          bsAlert.show();
          await router.navigate("/home");
        }
        return await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "DELETE",
        });
      }
    }
    return response;
  },
};
