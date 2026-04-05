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

  listBooks: async () => {
    const response = await api.get("/api/content/books");
    return response.data;
  },

  getNextSlide: async (bookId) => {
    const params = bookId ? { book_id: bookId } : {};
    const response = await api.get("/api/slides/next", { params });
    return response.data;
  },

  markChapterLearnt: async (chapterId) => {
    const response = await api.post(`/api/slides/chapters/${chapterId}/learnt`);
    return response.data;
  },

  respondToQuiz: async (quizId, body) => {
    const response = await api.post(
      `/api/slides/quizzes/${quizId}/respond`,
      body,
    );
    return response.data;
  },

  getActivityLog: async () => {
    const response = await api.get("/api/dashboard/activity-log");
    return response.data;
  },

  sendChatMessage: async (body) => {
    const response = await api.post("/api/slides/chat", body);
    return response.data;
  },

  getChatHistory: async (slideType, chapterId, quizId) => {
    const params = { slide_type: slideType };
    if (chapterId) params.chapter_id = chapterId;
    if (quizId) params.quiz_id = quizId;
    const response = await api.get("/api/slides/chat", { params });
    return response.data;
  },
};

export default apiService;
