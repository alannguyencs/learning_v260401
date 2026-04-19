import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const FavoriteChapterCard = ({ chapter }) => (
  <div className="bg-gray-700 rounded-lg p-6 border border-gray-600 relative">
    <div className="text-sm text-gray-400 mb-3">
      {chapter.book_title} &middot; {chapter.lesson_title}
      {chapter.chapter_index
        ? ` · Chapter ${chapter.chapter_index}`
        : ""}
    </div>

    <h2 className="text-xl font-bold text-white mb-4">{chapter.title}</h2>

    <div className="prose prose-invert max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {chapter.content}
      </ReactMarkdown>
    </div>
  </div>
);

export default FavoriteChapterCard;
