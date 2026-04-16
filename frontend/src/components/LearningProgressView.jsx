import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import apiService from "../services/api";

function AccuracyTrendline({ points }) {
  if (!points || points.length < 2) return null;

  const w = 400;
  const h = 120;
  const pad = { top: 10, right: 10, bottom: 20, left: 35 };
  const cw = w - pad.left - pad.right;
  const ch = h - pad.top - pad.bottom;

  const minY = Math.max(0, Math.min(...points) - 10);
  const maxY = Math.min(100, Math.max(...points) + 10);
  const rangeY = maxY - minY || 1;

  const toX = (i) => pad.left + (i / (points.length - 1)) * cw;
  const toY = (v) => pad.top + ch - ((v - minY) / rangeY) * ch;

  const pathD = points
    .map(
      (v, i) =>
        `${i === 0 ? "M" : "L"}${toX(i).toFixed(1)},${toY(v).toFixed(1)}`,
    )
    .join(" ");

  const yTicks = [minY, Math.round((minY + maxY) / 2), maxY];

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="w-full max-w-md"
      preserveAspectRatio="xMidYMid meet"
    >
      {yTicks.map((t) => (
        <g key={t}>
          <line
            x1={pad.left}
            x2={w - pad.right}
            y1={toY(t)}
            y2={toY(t)}
            stroke="#374151"
            strokeWidth="0.5"
          />
          <text
            x={pad.left - 4}
            y={toY(t) + 3}
            textAnchor="end"
            fill="#9CA3AF"
            fontSize="9"
          >
            {t}%
          </text>
        </g>
      ))}
      <path
        d={pathD}
        fill="none"
        stroke="#3B82F6"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {points.map((v, i) => (
        <circle key={i} cx={toX(i)} cy={toY(v)} r="2.5" fill="#3B82F6" />
      ))}
    </svg>
  );
}

function BookCard({ book }) {
  const hasAnswers = book.lessons.some((l) => l.total_answers > 0);

  return (
    <div className="rounded-lg border border-gray-600 bg-gray-800 p-5">
      <h2 className="text-lg font-bold text-white mb-4">{book.book_title}</h2>

      {hasAnswers && book.accuracy_trend.length >= 2 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 mb-1">Accuracy trend (recent)</p>
          <AccuracyTrendline points={book.accuracy_trend} />
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 text-left border-b border-gray-700">
              <th className="pb-2 pr-4 font-medium">Lesson</th>
              <th className="pb-2 pr-4 font-medium">Revision</th>
              <th className="pb-2 font-medium">Accuracy</th>
            </tr>
          </thead>
          <tbody>
            {book.lessons.map((lesson, i) => {
              const pct =
                lesson.total_answers > 0
                  ? Math.round(
                      (lesson.correct_answers / lesson.total_answers) * 100,
                    )
                  : null;
              return (
                <tr key={i} className="border-b border-gray-700/50">
                  <td className="py-2 pr-4 text-gray-300">
                    {lesson.lesson_title}
                  </td>
                  <td className="py-2 pr-4 text-gray-300 whitespace-nowrap">
                    {lesson.round_num != null ? (
                      <>
                        R{lesson.round_num} {lesson.round_status}
                      </>
                    ) : (
                      <span className="text-gray-500">&mdash;</span>
                    )}
                  </td>
                  <td className="py-2 text-gray-300 whitespace-nowrap">
                    {pct != null ? (
                      <>
                        {lesson.correct_answers}/{lesson.total_answers} = {pct}%
                      </>
                    ) : (
                      <span className="text-gray-500">&mdash;</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
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

  return (
    <div className="space-y-6">
      {data.map((book) => (
        <BookCard key={book.book_id} book={book} />
      ))}
    </div>
  );
};

export default LearningProgressView;
