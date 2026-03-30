import React, { useState } from "react";

const MC_OPTIONS = ["A", "B", "C", "D"];

const FeedbackPanel = ({ feedback, onNext }) => (
  <div className="mt-4" data-testid="feedback-panel">
    <div
      className={`text-lg font-bold mb-2 ${feedback.is_correct ? "text-green-400" : "text-red-400"}`}
    >
      {feedback.is_correct ? "\u2713 Correct" : "\u2717 Incorrect"}
    </div>
    {feedback.feedback && (
      <p className="text-gray-300 italic mb-4">{feedback.feedback}</p>
    )}
    <button
      onClick={onNext}
      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
    >
      Next Slide
    </button>
  </div>
);

const QuizSlide = ({ quiz, feedback, onSubmit, onSkip, onNext }) => {
  const [answer, setAnswer] = useState("");
  const isMC = quiz.quiz_type === "multiple_choice";
  const optionMap = {
    A: quiz.option_a,
    B: quiz.option_b,
    C: quiz.option_c,
    D: quiz.option_d,
  };

  const handleSubmit = () => {
    if (!answer.trim()) return;
    onSubmit(answer);
  };

  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <div className="text-sm text-gray-400 mb-2">
        Revision R{quiz.round_num} &middot; {quiz.lesson_title} &middot;{" "}
        {quiz.book_title}
      </div>
      <p className="text-lg text-white font-medium mb-4">{quiz.question}</p>

      {!feedback && (
        <>
          {isMC ? (
            <div className="space-y-2 mb-4">
              {MC_OPTIONS.filter((opt) => optionMap[opt]).map((opt) => (
                <label
                  key={opt}
                  className="flex items-center gap-3 text-gray-200 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="mc-answer"
                    value={opt}
                    checked={answer === opt}
                    onChange={() => setAnswer(opt)}
                    className="accent-blue-500"
                  />
                  <span>
                    {opt}. {optionMap[opt]}
                  </span>
                </label>
              ))}
            </div>
          ) : (
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={4}
              placeholder="Type your answer..."
              className="w-full px-3 py-2 bg-gray-800 text-gray-200 border border-gray-600 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          )}

          <div className="flex gap-3 justify-end">
            <button
              onClick={onSkip}
              className="px-4 py-2 text-gray-300 border border-gray-500 rounded hover:bg-gray-600 transition-colors"
            >
              Skip
            </button>
            <button
              onClick={handleSubmit}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Submit Answer
            </button>
          </div>
        </>
      )}

      {feedback && <FeedbackPanel feedback={feedback} onNext={onNext} />}
    </div>
  );
};

export default QuizSlide;
