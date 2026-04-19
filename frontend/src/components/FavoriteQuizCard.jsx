import React from "react";

const MC_OPTIONS = ["A", "B", "C", "D"];

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

export default FavoriteQuizCard;
