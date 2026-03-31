import React from "react";
import { Link } from "react-router-dom";
import useSlide from "../hooks/useSlide";
import BookSelector from "../components/BookSelector";
import ChapterSlide from "../components/ChapterSlide";
import QuizSlide from "../components/QuizSlide";
import AllCaughtUp from "../components/AllCaughtUp";

const SlidePage = () => {
  const {
    slide,
    loading,
    error,
    feedback,
    bookId,
    markLearnt,
    submitAnswer,
    skipItem,
    selectBook,
    fetchNextSlide,
  } = useSlide();

  return (
    <div className="min-h-screen bg-gray-800">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex justify-end mb-2">
          <Link
            to="/dashboard"
            className="text-sm text-gray-400 hover:text-gray-200 underline"
          >
            Activity Log
          </Link>
        </div>
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
            onSkip={() => fetchNextSlide(bookId)}
          />
        )}

        {!loading && !error && slide?.slide_type === "quiz" && (
          <QuizSlide
            quiz={slide.quiz}
            feedback={feedback}
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
    </div>
  );
};

export default SlidePage;
