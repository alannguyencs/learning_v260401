import { useState, useEffect, useCallback } from "react";
import apiService from "../services/api";

const useSlideChat = (slideType, chapterId, quizId) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadHistory = useCallback(async () => {
    if (!slideType) return;
    try {
      const data = await apiService.getChatHistory(
        slideType,
        chapterId,
        quizId,
      );
      setMessages(data);
    } catch {
      setMessages([]);
    }
  }, [slideType, chapterId, quizId]);

  useEffect(() => {
    setMessages([]);
    loadHistory();
  }, [loadHistory]);

  const sendMessage = async (text) => {
    const userMsg = {
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const data = await apiService.sendChatMessage({
        slide_type: slideType,
        chapter_id: chapterId || null,
        quiz_id: quizId || null,
        message: text,
      });
      const aiMsg = {
        role: "assistant",
        content: data.response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      const errMsg = {
        role: "assistant",
        content: "Sorry, I could not generate a response. Please try again.",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, loading, sendMessage };
};

export default useSlideChat;
