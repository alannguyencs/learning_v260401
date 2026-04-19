import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import apiService from "../services/api";
import BookSelector from "./BookSelector";
import FavoriteQuizCard from "./FavoriteQuizCard";
import FavoriteChapterCard from "./FavoriteChapterCard";

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

const itemBookId = (item) =>
  item.type === "quiz" ? item.quiz.book_id : item.chapter.book_id;

const FavoriteView = () => {
  const [items, setItems] = useState([]);
  const [index, setIndex] = useState(0);
  const [bookId, setBookId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiService
      .listLikedItems()
      .then((data) => setItems(data.items || []))
      .catch(() => setError("Failed to load favorites."))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(
    () =>
      bookId ? items.filter((item) => itemBookId(item) === bookId) : items,
    [items, bookId],
  );

  useEffect(() => {
    setIndex(0);
  }, [bookId]);

  const goPrev = () => setIndex((i) => Math.max(0, i - 1));
  const goNext = () => setIndex((i) => Math.min(filtered.length - 1, i + 1));

  if (loading) {
    return (
      <div className="text-center text-gray-400 py-16">
        Loading favorites...
      </div>
    );
  }

  if (error) {
    return <div className="bg-red-900 text-red-200 rounded p-4">{error}</div>;
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="mb-4">No favorites yet.</p>
        <Link
          to="/slides"
          className="text-blue-400 underline hover:text-blue-300"
        >
          Like a quiz or chapter from the Slides page to add it here
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
          {current.type === "quiz" ? (
            <FavoriteQuizCard quiz={current.quiz} />
          ) : (
            <FavoriteChapterCard chapter={current.chapter} />
          )}
          <ArrowDown onClick={goNext} disabled={atEnd} />
        </>
      )}
    </div>
  );
};

export default FavoriteView;
