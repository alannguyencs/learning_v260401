import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import LikeButton from "../../components/LikeButton";

describe("LikeButton", () => {
  it("renders outline heart when not liked (quiz)", () => {
    render(
      <LikeButton kind="quiz" id={42} isLiked={false} onToggle={jest.fn()} />,
    );
    const button = screen.getByRole("button", { name: /like quiz/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-pressed", "false");
  });

  it("renders filled heart when liked (quiz)", () => {
    render(<LikeButton kind="quiz" id={42} isLiked onToggle={jest.fn()} />);
    const button = screen.getByRole("button", { name: /unlike quiz/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-pressed", "true");
  });

  it("renders outline heart with chapter label when kind='chapter'", () => {
    render(
      <LikeButton
        kind="chapter"
        id={16}
        isLiked={false}
        onToggle={jest.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /like chapter/i }),
    ).toBeInTheDocument();
  });

  it("renders filled heart with chapter label when liked + chapter", () => {
    render(<LikeButton kind="chapter" id={16} isLiked onToggle={jest.fn()} />);
    expect(
      screen.getByRole("button", { name: /unlike chapter/i }),
    ).toBeInTheDocument();
  });

  it("calls onToggle with id on click", () => {
    const onToggle = jest.fn();
    render(
      <LikeButton kind="quiz" id={42} isLiked={false} onToggle={onToggle} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /like quiz/i }));
    expect(onToggle).toHaveBeenCalledWith(42);
  });

  it("falls back to quizId prop for backwards compat", () => {
    render(<LikeButton quizId={7} isLiked={false} onToggle={jest.fn()} />);
    expect(
      screen.getByRole("button", { name: /like quiz/i }),
    ).toBeInTheDocument();
  });
});
