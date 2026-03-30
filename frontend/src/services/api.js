import axios from "axios";

export const API_BASE_URL = process.env.REACT_APP_API_URL || "";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

const apiService = {
  login: async (username, password) => {
    const response = await api.post("/api/login/", { username, password });
    return response.data;
  },

  logout: async () => {
    const response = await api.post("/api/login/logout");
    return response.data;
  },

  getCurrentUser: async () => {
    try {
      const response = await api.get("/api/me");
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        return { authenticated: false };
      }
      throw error;
    }
  },
};

export default apiService;
