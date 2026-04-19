import { useCallback, useEffect, useState } from "react";
import apiService from "../services/api";

const useLikedSlides = () => {
  const [quizIds, setQuizIds] = useState(() => new Set());
  const [chapterIds, setChapterIds] = useState(() => new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await apiService.listLikedQuizzes();
        if (!cancelled) {
          setQuizIds(new Set(data.quiz_ids || []));
          setChapterIds(new Set(data.chapter_ids || []));
        }
      } catch {
        if (!cancelled) {
          setQuizIds(new Set());
          setChapterIds(new Set());
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const isLiked = useCallback(
    (kind, id) => {
      if (kind === "quiz") return quizIds.has(id);
      if (kind === "chapter") return chapterIds.has(id);
      return false;
    },
    [quizIds, chapterIds],
  );

  const toggleLike = useCallback(
    async (kind, id) => {
      const setter = kind === "quiz" ? setQuizIds : setChapterIds;
      const was = kind === "quiz" ? quizIds.has(id) : chapterIds.has(id);
      setter((prev) => {
        const next = new Set(prev);
        if (was) next.delete(id);
        else next.add(id);
        return next;
      });
      try {
        if (kind === "quiz") {
          if (was) await apiService.unlikeQuiz(id);
          else await apiService.likeQuiz(id);
        } else {
          if (was) await apiService.unlikeChapter(id);
          else await apiService.likeChapter(id);
        }
      } catch {
        setter((prev) => {
          const next = new Set(prev);
          if (was) next.add(id);
          else next.delete(id);
          return next;
        });
      }
    },
    [quizIds, chapterIds],
  );

  return { quizIds, chapterIds, loading, isLiked, toggleLike };
};

export default useLikedSlides;
