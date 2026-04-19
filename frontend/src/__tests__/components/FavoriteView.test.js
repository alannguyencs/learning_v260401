import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import FavoriteView from "../../components/FavoriteView";
import apiService from "../../services/api";

jest.mock("../../services/api");
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
jest.mock("../../components/BookSelector", () => ({ bookId, onSelect }) => (
  <select
    data-testid="book-selector"
    value={bookId ?? ""}
    onChange={(e) => onSelect(e.target.value || null)}
  >
    <option value="">All Books</option>
    <option value="bk1">Book 1</option>
    <option value="bk2">Book 2</option>
  </select>
));

const quizItem = {
  type: "quiz",
  id: 1,
  liked_at: "2026-04-19T12:00:00",
  quiz: {
    id: 42,
    chapter_id: 9,
    quiz_type: "multiple_choice",
    question: "What is ML?",
    option_a: "A",
    option_b: "B",
    option_c: "C",
    option_d: "D",
    expected_answer: null,
    lesson_id: 3,
    lesson_title: "Intro",
    book_id: "bk1",
    book_title: "Book 1",
    correct_options: ["A"],
    liked_at: "2026-04-19T12:00:00",
  },
};

const chapterItem = {
  type: "chapter",
  id: 2,
  liked_at: "2026-04-19T11:00:00",
  chapter: {
    id: 9,
    lesson_id: 3,
    lesson_title: "Intro",
    lesson_index: 1,
    chapter_index: 1,
    book_id: "bk2",
    book_title: "Book 2",
    title: "My Room",
    content: "# Heading\n\nSome markdown body.",
  },
};

const renderView = () =>
  render(
    <MemoryRouter>
      <FavoriteView />
    </MemoryRouter>,
  );

describe("FavoriteView (interleaved)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows empty state when no likes", async () => {
    apiService.listLikedItems.mockResolvedValue({ items: [] });
    renderView();
    await waitFor(() =>
      expect(screen.getByText(/No favorites yet/)).toBeInTheDocument(),
    );
    expect(
      screen.getByText(/Like a quiz or chapter from the Slides page/),
    ).toBeInTheDocument();
  });

  it("renders a quiz card for quiz items", async () => {
    apiService.listLikedItems.mockResolvedValue({ items: [quizItem] });
    renderView();
    await waitFor(() =>
      expect(screen.getByText("What is ML?")).toBeInTheDocument(),
    );
    // Quiz card breadcrumb contains book/lesson info separated by middot
    expect(screen.getByText(/Book 1 · Intro/)).toBeInTheDocument();
  });

  it("renders a chapter card for chapter items", async () => {
    apiService.listLikedItems.mockResolvedValue({ items: [chapterItem] });
    renderView();
    await waitFor(() =>
      expect(screen.getByText("My Room")).toBeInTheDocument(),
    );
    expect(screen.getByText(/Book 2 · Intro · Chapter 1/)).toBeInTheDocument();
  });

  it("paginates between quiz and chapter items", async () => {
    apiService.listLikedItems.mockResolvedValue({
      items: [quizItem, chapterItem],
    });
    renderView();
    await waitFor(() =>
      expect(screen.getByText("What is ML?")).toBeInTheDocument(),
    );
    expect(screen.getByText("1 / 2")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText(/Next favorite/));
    expect(screen.getByText("My Room")).toBeInTheDocument();
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
  });

  it("filters by book_id (applies to both types)", async () => {
    apiService.listLikedItems.mockResolvedValue({
      items: [quizItem, chapterItem],
    });
    renderView();
    await waitFor(() =>
      expect(screen.getByText("What is ML?")).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByTestId("book-selector"), {
      target: { value: "bk2" },
    });
    expect(screen.getByText("My Room")).toBeInTheDocument();
    expect(screen.queryByText("What is ML?")).not.toBeInTheDocument();
  });
});
