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

  getCurrentSlide: async (bookId) => {
    const params = bookId ? { book_id: bookId } : {};
    const response = await api.get("/api/slides/current", { params });
    return response.data;
  },

  slideForward: async (body) => {
    const response = await api.post("/api/slides/forward", body);
    return response.data;
  },

  slideBack: async () => {
    const response = await api.post("/api/slides/back");
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

  getLearningProgress: async () => {
    const response = await api.get("/api/dashboard/learning-progress");
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

  likeQuiz: async (quizId) => {
    const response = await api.post(`/api/slides/quizzes/${quizId}/like`);
    return response.data;
  },

  unlikeQuiz: async (quizId) => {
    const response = await api.delete(`/api/slides/quizzes/${quizId}/like`);
    return response.data;
  },

  listLikedQuizzes: async () => {
    const response = await api.get("/api/slides/likes");
    return response.data;
  },

  listLikedQuizzesFull: async () => {
    const response = await api.get("/api/slides/liked-quizzes");
    return response.data;
  },
};

export default apiService;
