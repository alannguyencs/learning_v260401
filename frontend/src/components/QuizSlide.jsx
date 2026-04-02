import React, { useState } from "react";

const MC_OPTIONS = ["A", "B", "C", "D"];

const TakeawayBlock = ({ text }) => {
  if (!text) return null;
  return (
    <div className="mt-3 p-3 bg-gray-900 border-l-4 border-blue-500 rounded">
      <p className="text-xs text-blue-400 font-semibold uppercase tracking-wide mb-1">
        Key Takeaway
      </p>
      <p className="text-gray-300 text-sm">{text}</p>
    </div>
  );
};

const KeyPointsList = ({ points, label }) => {
  if (!points || points.length === 0) return null;
  return (
    <div className="mt-3 p-3 bg-gray-900 rounded">
      <p className="text-xs text-yellow-400 font-semibold uppercase tracking-wide mb-2">
        {label}
      </p>
      <ul className="space-y-1">
        {points.map((pt, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
            <span className="text-yellow-500 mt-0.5">•</span>
            <span>{pt}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

const McOptionExplanations = ({
  optionMap,
  correctOptions,
  metadata,
  userAnswer,
}) => {
  if (!metadata) return null;
  const explMap = {
    A: metadata.response_to_user_option_a,
    B: metadata.response_to_user_option_b,
    C: metadata.response_to_user_option_c,
    D: metadata.response_to_user_option_d,
  };
  const correct = correctOptions || [];
  return (
    <div className="mt-3 space-y-2">
      {MC_OPTIONS.filter(
        (opt) =>
          optionMap[opt] && (opt === userAnswer || correct.includes(opt)),
      ).map((opt) => {
        const isCorrect = correct.includes(opt);
        const isUserPick = opt === userAnswer;
        const isWrongPick = isUserPick && !isCorrect;
        return (
          <div
            key={opt}
            className={`p-2 rounded text-sm border ${
              isCorrect
                ? "border-green-600 bg-green-900/20"
                : isWrongPick
                  ? "border-red-600 bg-red-900/20"
                  : "border-gray-600 bg-gray-800/40"
            }`}
          >
            <span
              className={`font-semibold ${
                isCorrect
                  ? "text-green-400"
                  : isWrongPick
                    ? "text-red-400"
                    : "text-gray-400"
              }`}
            >
              {opt}. {optionMap[opt]}
            </span>
            {explMap[opt] && (
              <p className="text-gray-400 text-xs mt-1">{explMap[opt]}</p>
            )}
          </div>
        );
      })}
    </div>
  );
};

const FeedbackPanel = ({ feedback, quiz, onNext, userAnswer }) => {
  const meta = quiz.quiz_metadata;
  const optionMap = {
    A: quiz.option_a,
    B: quiz.option_b,
    C: quiz.option_c,
    D: quiz.option_d,
  };

  return (
    <div className="mt-4" data-testid="feedback-panel">
      <div
        className={`text-lg font-bold mb-2 ${feedback.is_correct ? "text-green-400" : "text-red-400"}`}
      >
        {feedback.is_correct ? "\u2713 Correct" : "\u2717 Incorrect"}
      </div>
      {feedback.feedback && (
        <p className="text-gray-300 italic mb-2">{feedback.feedback}</p>
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

      <TakeawayBlock text={quiz.quiz_take_away} />

      <button
        onClick={onNext}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Next Slide
      </button>
    </div>
  );
};

const ClozeQuestion = ({ sentence, answer, onChange }) => {
  const parts = sentence.split("___");
  return (
    <p className="text-lg text-white font-medium mb-4 leading-relaxed">
      {parts.map((part, i) => (
        <React.Fragment key={i}>
          {part}
          {i < parts.length - 1 && (
            <input
              type="text"
              value={answer}
              onChange={(e) => onChange(e.target.value)}
              placeholder="..."
              className="inline-block mx-1 px-2 py-0.5 w-32 bg-gray-800 text-gray-200 border-b-2 border-blue-400 focus:outline-none focus:border-blue-300 text-base"
            />
          )}
        </React.Fragment>
      ))}
    </p>
  );
};

const QuizSlide = ({ quiz, feedback, onSubmit, onSkip, onNext }) => {
  const [answer, setAnswer] = useState("");
  const isMC = quiz.quiz_type === "multiple_choice";
  const isCloze = quiz.quiz_type === "cloze";
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
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm text-gray-400">
          Revision R{quiz.round_num} &middot; {quiz.lesson_title} &middot;{" "}
          {quiz.book_title}
        </div>
        {quiz.section_name && (
          <span className="text-xs px-2 py-0.5 bg-gray-600 text-gray-300 rounded-full">
            {quiz.section_name}
          </span>
        )}
      </div>

      {isCloze ? (
        <ClozeQuestion
          sentence={quiz.question}
          answer={answer}
          onChange={setAnswer}
        />
      ) : (
        <p className="text-lg text-white font-medium mb-4">{quiz.question}</p>
      )}

      {!feedback && (
        <>
          {isMC && (
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

      {feedback && (
        <FeedbackPanel
          feedback={feedback}
          quiz={quiz}
          onNext={onNext}
          userAnswer={answer}
        />
      )}
    </div>
  );
};

export default QuizSlide;
