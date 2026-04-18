import React from "react";
import useSlide from "../hooks/useSlide";
import useLikedQuizzes from "../hooks/useLikedQuizzes";
import BookSelector from "../components/BookSelector";
import ChatButton from "../components/ChatButton";
import LikeButton from "../components/LikeButton";
import ChapterSlide from "../components/ChapterSlide";
import QuizSlide from "../components/QuizSlide";
import AllCaughtUp from "../components/AllCaughtUp";

const ArrowUp = ({ onClick }) => (
  <button
    onClick={onClick}
    className="w-full flex justify-center py-1 text-gray-400 hover:text-blue-600 transition-colors"
    aria-label="Previous slide"
  >
    <svg
      className="w-6 h-6"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
    </svg>
  </button>
);

const ArrowDown = ({ onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-1 px-3 py-1 text-gray-400 hover:text-blue-600 transition-colors"
    aria-label="Next slide"
  >
    <svg
      className="w-6 h-6"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  </button>
);

const SlidePage = () => {
  const {
    slide,
    loading,
    error,
    feedback,
    submitting,
    bookId,
    hasPrevious,
    markLearnt,
    submitAnswer,
    skipItem,
    selectBook,
    fetchNextSlide,
    goPrevious,
  } = useSlide();

  const { isLiked, toggleLike } = useLikedQuizzes();

  const isActive = !loading && !error && slide && slide.slide_type !== "none";

  const handleDownArrow = () => {
    if (!slide) return;
    if (slide.slide_type === "chapter") {
      fetchNextSlide(slide.chapter.id);
    } else if (slide.slide_type === "quiz" && !feedback) {
      skipItem(slide.quiz.id, {
        round_num: slide.quiz.round_num,
        lesson_id: slide.quiz.lesson_id,
        user_answer: "",
        is_skip: true,
      });
    } else {
      fetchNextSlide();
    }
  };

  return (
    <div className="min-h-screen bg-gray-800">
      <div className="relative max-w-3xl mx-auto px-4 py-8">
        {isActive && hasPrevious && <ArrowUp onClick={goPrevious} />}

        <BookSelector bookId={bookId} onSelect={selectBook} />

        {loading && (
          <div className="text-center text-gray-400 py-12">Loading...</div>
        )}

        {error && (
          <div className="bg-red-900 text-red-200 rounded p-4 mb-4">
            {error}
          </div>
        )}

        {!loading && !error && slide?.slide_type === "chapter" && (
          <ChapterSlide
            chapter={slide.chapter}
            onMarkLearnt={() => markLearnt(slide.chapter.id)}
          />
        )}

        {!loading && !error && slide?.slide_type === "quiz" && (
          <QuizSlide
            quiz={slide.quiz}
            feedback={feedback}
            submitting={submitting}
            onSubmit={(answer) =>
              submitAnswer(slide.quiz.id, {
                round_num: slide.quiz.round_num,
                lesson_id: slide.quiz.lesson_id,
                user_answer: answer,
                is_skip: false,
              })
            }
          />
        )}

        {!loading && !error && slide?.slide_type === "none" && <AllCaughtUp />}

        {!loading && !error && slide && slide.slide_type !== "none" && (
          <ChatButton
            slideType={slide.slide_type}
            chapterId={slide.chapter?.id || null}
            quizId={slide.quiz?.id || null}
          />
        )}

        {!loading && !error && slide?.slide_type === "quiz" && slide.quiz && (
          <LikeButton
            quizId={slide.quiz.id}
            isLiked={isLiked(slide.quiz.id)}
            onToggle={toggleLike}
          />
        )}
      </div>

      {isActive && (
        <div className="fixed bottom-[76px] left-1/2 -translate-x-1/2 z-40">
          <ArrowDown onClick={handleDownArrow} />
        </div>
      )}
    </div>
  );
};

export default SlidePage;
