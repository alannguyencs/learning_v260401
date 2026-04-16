import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const ChapterSlide = ({ chapter, onMarkLearnt }) => (
  <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
    <div className="text-sm text-gray-400 mb-4">
      {chapter.book_title} &rsaquo; {chapter.lesson_title} &rsaquo; Chapter{" "}
      {chapter.chapter_index}
    </div>
    <h2 className="text-xl font-bold text-white mb-4">{chapter.title}</h2>
    <div className="prose prose-invert max-w-none mb-6">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {chapter.content}
      </ReactMarkdown>
    </div>
    <div className="flex gap-3 justify-end">
      <button
        onClick={onMarkLearnt}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Mark as Learnt
      </button>
    </div>
  </div>
);

export default ChapterSlide;
