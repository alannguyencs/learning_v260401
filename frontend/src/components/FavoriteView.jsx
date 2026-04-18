import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import apiService from "../services/api";
import BookSelector from "./BookSelector";

const MC_OPTIONS = ["A", "B", "C", "D"];

const ArrowUp = ({ onClick, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`w-full flex justify-center py-1 transition-colors ${
      disabled
        ? "text-gray-600 cursor-not-allowed"
        : "text-gray-400 hover:text-blue-400"
    }`}
    aria-label="Previous favorite"
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

const ArrowDown = ({ onClick, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`w-full flex justify-center py-1 transition-colors ${
      disabled
        ? "text-gray-600 cursor-not-allowed"
        : "text-gray-400 hover:text-blue-400"
    }`}
    aria-label="Next favorite"
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

const FavoriteQuizCard = ({ quiz }) => {
  const optionMap = {
    A: quiz.option_a,
    B: quiz.option_b,
    C: quiz.option_c,
    D: quiz.option_d,
  };
  const isMC = quiz.quiz_type === "multiple_choice";
  const correctSet = new Set(quiz.correct_options || []);

  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600 relative">
      <div className="text-sm text-gray-400 mb-3">
        {quiz.book_title} &middot; {quiz.lesson_title}
        {quiz.section_name ? ` · ${quiz.section_name}` : ""}
      </div>

      <p className="text-lg text-white font-medium mb-4">{quiz.question}</p>

      {isMC && (
        <div className="space-y-2 mb-4">
          {MC_OPTIONS.filter((opt) => optionMap[opt]).map((opt) => {
            const isCorrect = correctSet.has(opt);
            return (
              <div
                key={opt}
                className={`px-3 py-2 rounded border ${
                  isCorrect
                    ? "bg-green-900/40 border-green-700 text-green-200"
                    : "bg-gray-800 border-gray-600 text-gray-300"
                }`}
              >
                <span className="font-medium">{opt}.</span> {optionMap[opt]}
                {isCorrect && (
                  <span className="ml-2 text-xs text-green-400 uppercase tracking-wide">
                    correct
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {!isMC && quiz.expected_answer && (
        <div className="mt-3 p-3 bg-gray-900 border-l-4 border-green-500 rounded">
          <p className="text-xs text-green-400 font-semibold uppercase tracking-wide mb-1">
            Expected Answer
          </p>
          <p className="text-gray-200 text-sm whitespace-pre-wrap">
            {quiz.expected_answer}
          </p>
        </div>
      )}

      {quiz.quiz_take_away && (
        <div className="mt-3 p-3 bg-gray-900 border-l-4 border-blue-500 rounded">
          <p className="text-xs text-blue-400 font-semibold uppercase tracking-wide mb-1">
            Key Takeaway
          </p>
          <p className="text-gray-300 text-sm">{quiz.quiz_take_away}</p>
        </div>
      )}
    </div>
  );
};

const FavoriteView = () => {
  const [quizzes, setQuizzes] = useState([]);
  const [index, setIndex] = useState(0);
  const [bookId, setBookId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiService
      .listLikedQuizzesFull()
      .then((data) => setQuizzes(data.quizzes))
      .catch(() => setError("Failed to load favorites."))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(
    () => (bookId ? quizzes.filter((q) => q.book_id === bookId) : quizzes),
    [quizzes, bookId],
  );

  useEffect(() => {
    setIndex(0);
  }, [bookId]);

  const goPrev = () => setIndex((i) => Math.max(0, i - 1));
  const goNext = () => setIndex((i) => Math.min(filtered.length - 1, i + 1));

  if (loading) {
    return (
      <div className="text-center text-gray-400 py-16">Loading favorites...</div>
    );
  }

  if (error) {
    return <div className="bg-red-900 text-red-200 rounded p-4">{error}</div>;
  }

  if (quizzes.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="mb-4">No favorites yet.</p>
        <Link
          to="/slides"
          className="text-blue-400 underline hover:text-blue-300"
        >
          Like a quiz from the Slides page to add it here
        </Link>
      </div>
    );
  }

  const safeIndex = Math.min(index, Math.max(0, filtered.length - 1));
  const current = filtered[safeIndex];
  const atStart = safeIndex === 0;
  const atEnd = filtered.length === 0 || safeIndex === filtered.length - 1;

  return (
    <div className="max-w-3xl mx-auto">
      <BookSelector bookId={bookId} onSelect={setBookId} />

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          No favorites in this book yet.
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
            <span>
              {safeIndex + 1} / {filtered.length}
            </span>
            <span>Newest liked first</span>
          </div>

          <ArrowUp onClick={goPrev} disabled={atStart} />
          <FavoriteQuizCard quiz={current} />
          <ArrowDown onClick={goNext} disabled={atEnd} />
        </>
      )}
    </div>
  );
};

export default FavoriteView;
