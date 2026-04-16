import React from "react";

const MC_OPTIONS = ["A", "B", "C", "D"];

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
  const userPicks = userAnswer ? userAnswer.split(",") : [];
  return (
    <div className="mt-3 space-y-2">
      {MC_OPTIONS.filter((opt) => optionMap[opt]).map((opt) => {
        const isCorrect = correct.includes(opt);
        const isWrongPick = userPicks.includes(opt) && !isCorrect;
        const border = isCorrect
          ? "border-green-600 bg-green-900/20"
          : isWrongPick
            ? "border-red-600 bg-red-900/20"
            : "border-gray-600 bg-gray-800/40";
        const text = isCorrect
          ? "text-green-400"
          : isWrongPick
            ? "text-red-400"
            : "text-gray-400";
        return (
          <div key={opt} className={`p-2 rounded text-sm border ${border}`}>
            <span className={`font-semibold ${text}`}>
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

export default McOptionExplanations;
