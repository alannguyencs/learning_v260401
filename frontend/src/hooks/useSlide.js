import { useState, useEffect, useCallback } from "react";
import apiService from "../services/api";

const useSlide = () => {
  const [slide, setSlide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [bookId, setBookId] = useState(null);

  const fetchNextSlide = useCallback(async (currentBookId) => {
    setLoading(true);
    setError(null);
    setFeedback(null);
    try {
      const data = await apiService.getNextSlide(currentBookId);
      setSlide(data);
    } catch {
      setError("Failed to load next slide.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNextSlide(null);
  }, [fetchNextSlide]);

  const markLearnt = async (chapterId) => {
    try {
      await apiService.markChapterLearnt(chapterId);
      await fetchNextSlide(bookId);
    } catch {
      setError("Failed to mark chapter as learnt.");
    }
  };

  const submitAnswer = async (quizId, body) => {
    try {
      const data = await apiService.respondToQuiz(quizId, body);
      setFeedback(data);
    } catch {
      setError("Failed to submit answer.");
    }
  };

  const skipItem = async (quizId, body) => {
    try {
      await apiService.respondToQuiz(quizId, body);
      await fetchNextSlide(bookId);
    } catch {
      setError("Failed to skip item.");
    }
  };

  const selectBook = useCallback(
    (newBookId) => {
      setBookId(newBookId);
      fetchNextSlide(newBookId);
    },
    [fetchNextSlide],
  );

  return {
    slide,
    loading,
    error,
    feedback,
    bookId,
    fetchNextSlide,
    markLearnt,
    submitAnswer,
    skipItem,
    selectBook,
  };
};

export default useSlide;
