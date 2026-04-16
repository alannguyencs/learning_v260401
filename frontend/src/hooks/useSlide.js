import { useState, useEffect, useCallback } from "react";
import apiService from "../services/api";

const useSlide = () => {
  const [slide, setSlide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [bookId, setBookId] = useState(null);
  const [hasPrevious, setHasPrevious] = useState(false);

  const _applySlideData = (data) => {
    setSlide(data);
    setHasPrevious(data.has_previous || false);
    setFeedback(data.feedback || null);
  };

  const loadCurrent = useCallback(async (currentBookId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getCurrentSlide(currentBookId);
      _applySlideData(data);
    } catch {
      setError("Failed to load slide.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrent(null);
  }, [loadCurrent]);

  const fetchNextSlide = useCallback(async (currentBookId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.slideForward({
        book_id: currentBookId || null,
      });
      _applySlideData(data);
    } catch {
      setError("Failed to load next slide.");
    } finally {
      setLoading(false);
    }
  }, []);

  const markLearnt = async (chapterId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.slideForward({
        book_id: bookId || null,
        mark_chapter_id: chapterId,
      });
      _applySlideData(data);
    } catch {
      setError("Failed to mark chapter as learnt.");
    } finally {
      setLoading(false);
    }
  };

  const goPrevious = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.slideBack();
      _applySlideData(data);
    } catch {
      setError("Failed to go to previous slide.");
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async (quizId, body) => {
    setSubmitting(true);
    try {
      const data = await apiService.respondToQuiz(quizId, body);
      setFeedback(data);
    } catch {
      setError("Failed to submit answer.");
    } finally {
      setSubmitting(false);
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
      loadCurrent(newBookId);
    },
    [loadCurrent],
  );

  return {
    slide,
    loading,
    error,
    feedback,
    submitting,
    bookId,
    hasPrevious,
    fetchNextSlide,
    markLearnt,
    goPrevious,
    submitAnswer,
    skipItem,
    selectBook,
  };
};

export default useSlide;
