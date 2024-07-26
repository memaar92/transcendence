const API_BASE_URL = 'api';

export const api = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    return response;
  },
  
  post: async (endpoint, data) => {
    console.log(JSON.stringify(data));
    console.log(`${API_BASE_URL}${endpoint}`);
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    console.log(response.status);
    return response;
  },

  delete: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE'
    });
    return response;
  }
};
