import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import apiService from "../services/api";

const ACTION_STYLES = {
  "LEARNT CHAPTER": "font-bold text-green-400",
  SKIP: "text-gray-400",
  ANSWER: "text-blue-400",
};

function actionClass(action) {
  if (ACTION_STYLES[action]) return ACTION_STYLES[action];
  if (action.startsWith("ROUND CREATED")) return "italic text-gray-500";
  return "text-gray-300";
}

function AnswerBadge({ value }) {
  if (!value) return <span className="text-gray-500">—</span>;
  if (value === "correct")
    return <span className="text-green-400 font-medium">correct</span>;
  return <span className="text-red-400 font-medium">wrong</span>;
}

function formatTime(raw) {
  if (!raw) return "—";
  const d = new Date(raw);
  return d.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDate(raw) {
  if (!raw) return "—";
  const d = new Date(raw);
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

const DashboardPage = () => {
  const [log, setLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiService
      .getActivityLog()
      .then((data) => setLog(data))
      .catch(() => setError("Failed to load activity log."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-800 text-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">Activity Log</h1>
          <Link
            to="/slides"
            className="text-sm text-gray-400 hover:text-gray-200 underline"
          >
            ← Back to Slides
          </Link>
        </div>

        {loading && (
          <div className="text-center text-gray-400 py-16">Loading...</div>
        )}

        {error && (
          <div className="bg-red-900 text-red-200 rounded p-4 mb-4">
            {error}
          </div>
        )}

        {!loading && !error && log.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="mb-4">No activity yet.</p>
            <Link
              to="/slides"
              className="text-blue-400 underline hover:text-blue-300"
            >
              Start learning on the Slides page
            </Link>
          </div>
        )}

        {!loading && !error && log.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-gray-700">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-900 text-gray-400 text-left">
                  <th className="px-3 py-3 font-medium">#</th>
                  <th className="px-3 py-3 font-medium">Date</th>
                  <th className="px-3 py-3 font-medium">Time</th>
                  <th className="px-3 py-3 font-medium">Action</th>
                  <th className="px-3 py-3 font-medium">book_id</th>
                  <th className="px-3 py-3 font-medium">lesson_index</th>
                  <th className="px-3 py-3 font-medium">lesson_title</th>
                  <th className="px-3 py-3 font-medium">chapter_id</th>
                  <th className="px-3 py-3 font-medium">answer_result</th>
                  <th className="px-3 py-3 font-medium">recall_rate</th>
                </tr>
              </thead>
              <tbody>
                {log.map((row, i) => (
                  <tr
                    key={i}
                    className={`border-t border-gray-700 ${
                      i % 2 === 0 ? "bg-gray-800" : "bg-gray-750"
                    } hover:bg-gray-700 transition-colors`}
                  >
                    <td className="px-3 py-2 text-gray-500">{i + 1}</td>
                    <td className="px-3 py-2 text-gray-400 whitespace-nowrap">
                      {formatDate(row.event_time)}
                    </td>
                    <td className="px-3 py-2 text-gray-300 whitespace-nowrap font-mono">
                      {formatTime(row.event_time)}
                    </td>
                    <td
                      className={`px-3 py-2 whitespace-nowrap ${actionClass(row.action)}`}
                    >
                      {row.action}
                    </td>
                    <td className="px-3 py-2 text-gray-300">
                      {row.book_id ?? <span className="text-gray-500">—</span>}
                    </td>
                    <td className="px-3 py-2 text-gray-300 text-center">
                      {row.lesson_index ?? (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-gray-300 max-w-xs truncate">
                      {row.lesson_title ?? (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-gray-300 text-center">
                      {row.chapter_id ?? (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <AnswerBadge value={row.answer_result} />
                    </td>
                    <td className="px-3 py-2 text-gray-300 text-center font-mono">
                      {row.recall_rate != null ? (
                        row.recall_rate.toFixed(2)
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
