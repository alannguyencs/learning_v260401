import { useCallback, useEffect, useState } from "react";
import apiService from "../services/api";

const useLikedQuizzes = () => {
  const [likedIds, setLikedIds] = useState(() => new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await apiService.listLikedQuizzes();
        if (!cancelled) {
          setLikedIds(new Set(data.quiz_ids || []));
        }
      } catch {
        if (!cancelled) setLikedIds(new Set());
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const isLiked = useCallback((quizId) => likedIds.has(quizId), [likedIds]);

  const toggleLike = useCallback(
    async (quizId) => {
      const wasLiked = likedIds.has(quizId);
      setLikedIds((prev) => {
        const next = new Set(prev);
        if (wasLiked) next.delete(quizId);
        else next.add(quizId);
        return next;
      });
      try {
        if (wasLiked) {
          await apiService.unlikeQuiz(quizId);
        } else {
          await apiService.likeQuiz(quizId);
        }
      } catch {
        setLikedIds((prev) => {
          const next = new Set(prev);
          if (wasLiked) next.add(quizId);
          else next.delete(quizId);
          return next;
        });
      }
    },
    [likedIds],
  );

  return { likedIds, loading, isLiked, toggleLike };
};

export default useLikedQuizzes;
