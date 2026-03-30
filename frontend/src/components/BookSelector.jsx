import React, { useEffect, useState } from "react";
import apiService from "../services/api";

const BookSelector = ({ bookId, onSelect }) => {
  const [books, setBooks] = useState([]);

  useEffect(() => {
    apiService
      .listBooks()
      .then(setBooks)
      .catch(() => {});
  }, []);

  return (
    <div className="mb-6 flex items-center gap-3">
      <label htmlFor="book-select" className="text-gray-300 font-medium">
        Book:
      </label>
      <select
        id="book-select"
        value={bookId || ""}
        onChange={(e) => onSelect(e.target.value || null)}
        className="px-3 py-1 bg-gray-700 text-gray-200 border border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All Books</option>
        {books.map((book) => (
          <option key={book.book_id} value={book.book_id}>
            {book.title}
          </option>
        ))}
      </select>
    </div>
  );
};

export default BookSelector;
