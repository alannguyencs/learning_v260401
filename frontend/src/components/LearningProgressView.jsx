import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import apiService from "../services/api";

function recallColor(rate) {
  if (rate < 0.5) return "text-green-400";
  if (rate <= 1.0) return "text-yellow-400";
  return "text-red-400";
}

function ProgressBar({ learnt, total }) {
  const pct = total > 0 ? Math.round((learnt / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-green-500 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm text-gray-300 whitespace-nowrap">
        {learnt}/{total} ({pct}%)
      </span>
    </div>
  );
}

function LessonCard({ lesson }) {
  const notStarted =
    lesson.learnt_chapters === 0 &&
    lesson.round_num == null &&
    lesson.total_answers === 0;

  return (
    <div
      className={`rounded-lg border p-4 ${
        notStarted
          ? "border-gray-700 bg-gray-800/50"
          : "border-gray-600 bg-gray-800"
      }`}
    >
      <h3 className="text-base font-semibold text-white mb-3">
        Lesson {lesson.lesson_index}: {lesson.lesson_title}
      </h3>

      {notStarted ? (
        <p className="text-sm text-gray-500 italic">Not started</p>
      ) : (
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 w-20">Chapters</span>
            <div className="flex-1">
              <ProgressBar
                learnt={lesson.learnt_chapters}
                total={lesson.total_chapters}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-gray-400 w-20">Revision</span>
            <span className="text-gray-300">
              {lesson.round_num != null ? (
                <>
                  R{lesson.round_num} {lesson.round_status}
                  {lesson.quizzes_in_round != null &&
                    ` \u00B7 ${lesson.round_quizzes_answered}/${lesson.quizzes_in_round} answered`}
                </>
              ) : (
                <span className="text-gray-500">No revision yet</span>
              )}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-gray-400 w-20">Accuracy</span>
            <span className="text-gray-300">
              {lesson.total_answers > 0 ? (
                <>
                  {lesson.correct_answers}/{lesson.total_answers} correct (
                  {Math.round(
                    (lesson.correct_answers / lesson.total_answers) * 100,
                  )}
                  %)
                </>
              ) : (
                <span className="text-gray-500">No quizzes yet</span>
              )}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-gray-400 w-20">Recall</span>
            {lesson.avg_forgetting_rate != null ? (
              <span className={recallColor(lesson.avg_forgetting_rate)}>
                avg {lesson.avg_forgetting_rate.toFixed(2)}
              </span>
            ) : (
              <span className="text-gray-500">&mdash;</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function groupByBook(lessons) {
  const books = {};
  for (const lesson of lessons) {
    if (!books[lesson.book_id]) {
      books[lesson.book_id] = {
        book_id: lesson.book_id,
        book_title: lesson.book_title,
        lessons: [],
      };
    }
    books[lesson.book_id].lessons.push(lesson);
  }
  return Object.values(books);
}

const LearningProgressView = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiService
      .getLearningProgress()
      .then((d) => setData(d))
      .catch(() => setError("Failed to load learning progress."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center text-gray-400 py-16">Loading...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-900 text-red-200 rounded p-4 mb-4">{error}</div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="mb-4">No lessons available yet.</p>
        <Link
          to="/slides"
          className="text-blue-400 underline hover:text-blue-300"
        >
          Start learning on the Slides page
        </Link>
      </div>
    );
  }

  const books = groupByBook(data);

  return (
    <div className="space-y-8">
      {books.map((book) => (
        <div key={book.book_id}>
          <h2 className="text-lg font-bold text-gray-300 mb-3">
            {book.book_title}
          </h2>
          <div className="space-y-3">
            {book.lessons.map((lesson) => (
              <LessonCard key={lesson.lesson_id} lesson={lesson} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default LearningProgressView;
