import React, { useState } from "react";

import McOptionExplanations from "./McOptionExplanations";

const MC_OPTIONS = ["A", "B", "C", "D"];

const COLOR_MAP = {
  yellow: { label: "text-yellow-400", bullet: "text-yellow-500" },
  green: { label: "text-green-400", bullet: "text-green-500" },
  red: { label: "text-red-400", bullet: "text-red-500" },
};

const KeyPointsList = ({ points, label, color = "yellow" }) => {
  if (!points || points.length === 0) return null;
  const colors = COLOR_MAP[color] || COLOR_MAP.yellow;
  return (
    <div className="mt-3 p-3 bg-gray-900 rounded">
      <p
        className={`text-xs ${colors.label} font-semibold uppercase tracking-wide mb-2`}
      >
        {label}
      </p>
      <ul className="space-y-1">
        {points.map((pt, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
            <span className={`${colors.bullet} mt-0.5`}>•</span>
            <span>{pt}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

const FeedbackPanel = ({ feedback, quiz, userAnswer }) => {
  const meta = quiz.quiz_metadata;
  const optionMap = {
    A: quiz.option_a,
    B: quiz.option_b,
    C: quiz.option_c,
    D: quiz.option_d,
  };
  const goodCount = feedback.good_points?.length || 0;
  const badCount = feedback.bad_points?.length || 0;
  const totalPoints = goodCount + badCount;

  return (
    <div className="mt-4" data-testid="feedback-panel">
      <div
        className={`text-lg font-bold mb-2 ${feedback.is_correct ? "text-green-400" : "text-red-400"}`}
      >
        {feedback.is_correct ? "\u2713 PASSED" : "\u2717 FAILED"}
      </div>

      {totalPoints > 0 && (
        <p className="text-gray-400 text-sm mb-2">
          {goodCount}/{totalPoints} points
        </p>
      )}

      {feedback.good_points?.length > 0 && (
        <KeyPointsList
          points={feedback.good_points}
          label="Good Points"
          color="green"
        />
      )}

      {feedback.bad_points?.length > 0 && (
        <KeyPointsList
          points={feedback.bad_points}
          label="Missed Points"
          color="red"
        />
      )}

      {quiz.quiz_type === "cloze" &&
        !feedback.is_correct &&
        quiz.expected_answer && (
          <div className="mt-3 p-3 bg-gray-900 border-l-4 border-yellow-500 rounded">
            <p className="text-xs text-yellow-400 font-semibold uppercase tracking-wide mb-1">
              Correct Answer
            </p>
            <p className="text-gray-200 text-sm font-medium">
              {quiz.expected_answer}
            </p>
          </div>
        )}

      {quiz.quiz_type === "multiple_choice" && (
        <McOptionExplanations
          optionMap={optionMap}
          correctOptions={quiz.correct_options}
          metadata={meta}
          userAnswer={userAnswer}
        />
      )}

      {quiz.quiz_type === "free_recall" && meta?.key_points && (
        <KeyPointsList points={meta.key_points} label="Key Points" />
      )}

      {quiz.quiz_type === "teach_back" && meta?.key_elements && (
        <KeyPointsList points={meta.key_elements} label="Key Elements" />
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

const QuizSlide = ({
  quiz,
  feedback,
  submitting,
  onSubmit,
  onJumpToChapter,
}) => {
  const [answer, setAnswer] = useState("");
  const isMC = quiz.quiz_type === "multiple_choice";
  const isCloze = quiz.quiz_type === "cloze";
  const isMultiMC = isMC && (quiz.correct_options?.length || 0) > 1;
  const optionMap = {
    A: quiz.option_a,
    B: quiz.option_b,
    C: quiz.option_c,
    D: quiz.option_d,
  };

  const toggleOption = (opt) => {
    const current = answer ? answer.split(",") : [];
    const next = current.includes(opt)
      ? current.filter((o) => o !== opt)
      : [...current, opt];
    setAnswer(next.sort().join(","));
  };

  const handleSubmit = () => answer.trim() && !submitting && onSubmit(answer);

  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <div className="text-sm text-gray-400 mb-2">
        Revision R{quiz.round_num} &middot; {quiz.lesson_title} &middot;{" "}
        {quiz.book_title}
      </div>

      {quiz.chapter_id && quiz.chapter_title && onJumpToChapter && (
        <button
          type="button"
          onClick={() => onJumpToChapter(quiz.chapter_id)}
          data-testid="view-chapter-link"
          className="text-sm text-blue-400 hover:text-blue-300 underline underline-offset-2 mb-4 inline-block text-left py-1"
        >
          View chapter: {quiz.chapter_title}
        </button>
      )}

      {isCloze ? (
        <p className="text-lg text-white font-medium mb-4 leading-relaxed">
          {quiz.question.split("___").map((part, i, arr) => (
            <React.Fragment key={i}>
              {part}
              {i < arr.length - 1 && (
                <input
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSubmit();
                  }}
                  placeholder="..."
                  className="inline-block mx-1 px-2 py-0.5 w-32 bg-gray-800 text-gray-200 border-b-2 border-blue-400 focus:outline-none focus:border-blue-300 text-base"
                />
              )}
            </React.Fragment>
          ))}
        </p>
      ) : (
        <p className="text-lg text-white font-medium mb-4">{quiz.question}</p>
      )}

      {!feedback && (
        <>
          {isMC && (
            <div className="space-y-2 mb-4">
              {isMultiMC && (
                <p className="text-xs text-gray-400 mb-1">
                  Select all that apply
                </p>
              )}
              {MC_OPTIONS.filter((opt) => optionMap[opt]).map((opt) => (
                <label
                  key={opt}
                  className="flex items-center gap-3 text-gray-200 cursor-pointer"
                >
                  <input
                    type={isMultiMC ? "checkbox" : "radio"}
                    name="mc-answer"
                    value={opt}
                    checked={
                      isMultiMC
                        ? answer.split(",").includes(opt)
                        : answer === opt
                    }
                    onChange={() =>
                      isMultiMC ? toggleOption(opt) : setAnswer(opt)
                    }
                    className="accent-blue-500"
                  />
                  <span>
                    {opt}. {optionMap[opt]}
                  </span>
                </label>
              ))}
            </div>
          )}

          {!isMC && !isCloze && (
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={4}
              placeholder="Type your answer..."
              className="w-full px-3 py-2 bg-gray-800 text-gray-200 border border-gray-600 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          )}

          <div className="flex gap-3 justify-end mt-4">
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className={`px-4 py-2 text-white rounded transition-colors ${submitting ? "bg-blue-800 cursor-not-allowed opacity-60" : "bg-blue-600 hover:bg-blue-700"}`}
            >
              {submitting ? "Submitting..." : "Submit Answer"}
            </button>
          </div>
        </>
      )}

      {feedback && (
        <FeedbackPanel feedback={feedback} quiz={quiz} userAnswer={answer} />
      )}
    </div>
  );
};

export default QuizSlide;
