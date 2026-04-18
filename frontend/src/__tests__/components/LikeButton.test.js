import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import LikeButton from "../../components/LikeButton";

describe("LikeButton", () => {
  it("renders outline heart when not liked (aria-label 'Like quiz')", () => {
    render(<LikeButton quizId={42} isLiked={false} onToggle={jest.fn()} />);
    const button = screen.getByRole("button", { name: /like quiz/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-pressed", "false");
  });

  it("renders filled heart when liked (aria-label 'Unlike quiz')", () => {
    render(<LikeButton quizId={42} isLiked onToggle={jest.fn()} />);
    const button = screen.getByRole("button", { name: /unlike quiz/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-pressed", "true");
  });

  it("calls onToggle with quizId on click", () => {
    const onToggle = jest.fn();
    render(<LikeButton quizId={42} isLiked={false} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole("button", { name: /like quiz/i }));
    expect(onToggle).toHaveBeenCalledWith(42);
  });
});
