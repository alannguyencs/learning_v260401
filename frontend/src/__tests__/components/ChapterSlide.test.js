import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import ChapterSlide from "../../components/ChapterSlide";

jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);

const mockChapter = {
  id: 1,
  book_title: "Machine Learning",
  lesson_title: "Intro",
  chapter_index: 1,
  title: "What is ML",
  content: "# Hello\nMachine learning is a field of AI.",
};

describe("ChapterSlide", () => {
  it("renders chapter title and content", () => {
    render(<ChapterSlide chapter={mockChapter} onMarkLearnt={jest.fn()} />);
    expect(screen.getByText("What is ML")).toBeInTheDocument();
    expect(screen.getByText(/Machine learning is/)).toBeInTheDocument();
  });

  it("calls onMarkLearnt when Mark as Learnt is clicked", () => {
    const onMarkLearnt = jest.fn();
    render(<ChapterSlide chapter={mockChapter} onMarkLearnt={onMarkLearnt} />);
    fireEvent.click(screen.getByText("Mark as Learnt"));
    expect(onMarkLearnt).toHaveBeenCalledTimes(1);
  });

  it("renders only Mark as Learnt button (no Skip Chapter)", () => {
    render(<ChapterSlide chapter={mockChapter} onMarkLearnt={jest.fn()} />);
    expect(screen.getByText("Mark as Learnt")).toBeInTheDocument();
    expect(screen.queryByText("Skip Chapter")).not.toBeInTheDocument();
  });
});
