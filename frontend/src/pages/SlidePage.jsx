import React from "react";
import { Link } from "react-router-dom";
import useSlide from "../hooks/useSlide";
import BookSelector from "../components/BookSelector";
import ChatButton from "../components/ChatButton";
import ChapterSlide from "../components/ChapterSlide";
import QuizSlide from "../components/QuizSlide";
import AllCaughtUp from "../components/AllCaughtUp";

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

  const showNavArrows =
    !loading && !error && slide && slide.slide_type !== "none";

  return (
    <div className="min-h-screen bg-gray-800">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex justify-end mb-2">
          <Link
            to="/dashboard"
            className="text-sm text-gray-400 hover:text-gray-200 underline"
          >
            Dashboard
          </Link>
        </div>
        <BookSelector bookId={bookId} onSelect={selectBook} />

        {showNavArrows && (
          <div className="flex justify-between items-center mb-4">
            {hasPrevious ? (
              <button
                onClick={goPrevious}
                disabled={loading || submitting}
                className="p-2 rounded-full bg-gray-700 hover:bg-gray-600 text-gray-200 disabled:opacity-40"
                aria-label="Previous slide"
              >
                ↑
              </button>
            ) : (
              <div className="w-10" />
            )}
            <button
              onClick={() => fetchNextSlide(bookId)}
              disabled={loading || submitting}
              className="p-2 rounded-full bg-gray-700 hover:bg-gray-600 text-gray-200 disabled:opacity-40"
              aria-label="Next slide"
            >
              ↓
            </button>
          </div>
        )}

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
            onSkip={() => fetchNextSlide(bookId)}
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
            onSkip={() =>
              skipItem(slide.quiz.id, {
                round_num: slide.quiz.round_num,
                lesson_id: slide.quiz.lesson_id,
                user_answer: "",
                is_skip: true,
              })
            }
            onNext={() => fetchNextSlide(bookId)}
          />
        )}

        {!loading && !error && slide?.slide_type === "none" && <AllCaughtUp />}
      </div>

      {!loading && !error && slide && slide.slide_type !== "none" && (
        <ChatButton
          slideType={slide.slide_type}
          chapterId={slide.chapter?.id || null}
          quizId={slide.quiz?.id || null}
        />
      )}
    </div>
  );
};

export default SlidePage;
