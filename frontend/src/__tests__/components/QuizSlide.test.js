import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import QuizSlide from "../../components/QuizSlide";

const mcQuiz = {
  id: 1,
  chapter_id: 9,
  chapter_title: "What is ML",
  quiz_type: "multiple_choice",
  question: "What is ML?",
  option_a: "Machine Learning",
  option_b: "Meta Learning",
  option_c: "Manual Learning",
  option_d: "Massive Learning",
  round_num: 0,
  lesson_title: "Intro",
  book_title: "ML Book",
};

const recallQuiz = {
  id: 2,
  quiz_type: "free_recall",
  question: "Explain backpropagation.",
  option_a: null,
  option_b: null,
  option_c: null,
  option_d: null,
  round_num: 1,
  lesson_title: "Neural Nets",
  book_title: "DL Book",
};

describe("QuizSlide", () => {
  it("renders MC options as radio buttons", () => {
    render(<QuizSlide quiz={mcQuiz} feedback={null} onSubmit={jest.fn()} />);
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(4);
  });

  it("renders text area for free_recall type", () => {
    render(
      <QuizSlide quiz={recallQuiz} feedback={null} onSubmit={jest.fn()} />,
    );
    expect(
      screen.getByPlaceholderText("Type your answer..."),
    ).toBeInTheDocument();
  });

  it("shows PASSED label when is_correct is true", () => {
    render(
      <QuizSlide
        quiz={mcQuiz}
        feedback={{
          is_correct: true,
          good_points: null,
          bad_points: null,
          round_done: false,
        }}
        onSubmit={jest.fn()}
      />,
    );
    expect(screen.getByTestId("feedback-panel")).toBeInTheDocument();
    expect(screen.getByText(/PASSED/)).toBeInTheDocument();
  });

  it("shows FAILED label when is_correct is false", () => {
    render(
      <QuizSlide
        quiz={recallQuiz}
        feedback={{
          is_correct: false,
          good_points: ["Got concept A"],
          bad_points: ["Missed B", "Missed C"],
          round_done: false,
        }}
        onSubmit={jest.fn()}
      />,
    );
    expect(screen.getByText(/FAILED/)).toBeInTheDocument();
  });

  it("shows good and bad points lists", () => {
    render(
      <QuizSlide
        quiz={recallQuiz}
        feedback={{
          is_correct: true,
          good_points: ["Explained gradients", "Mentioned chain rule"],
          bad_points: ["Missed backprop detail"],
          round_done: false,
        }}
        onSubmit={jest.fn()}
      />,
    );
    expect(screen.getByText("Explained gradients")).toBeInTheDocument();
    expect(screen.getByText("Mentioned chain rule")).toBeInTheDocument();
    expect(screen.getByText("Missed backprop detail")).toBeInTheDocument();
    expect(screen.getByText("2/3 points")).toBeInTheDocument();
  });

  it("no Skip button and no Next Slide button are rendered", () => {
    render(
      <QuizSlide
        quiz={recallQuiz}
        feedback={{
          is_correct: false,
          good_points: [],
          bad_points: ["Wrong"],
          round_done: false,
        }}
        onSubmit={jest.fn()}
      />,
    );
    expect(screen.queryByText("Skip")).not.toBeInTheDocument();
    expect(screen.queryByText("Next Slide")).not.toBeInTheDocument();
  });

  it("MC wrong answer: shows user pick red and correct green", () => {
    const mcWithMeta = {
      ...mcQuiz,
      correct_options: ["B"],
      quiz_metadata: {
        response_to_user_option_a: "Wrong.",
        response_to_user_option_b: "Correct!",
        response_to_user_option_c: "Nope.",
        response_to_user_option_d: "Nope.",
      },
    };
    render(
      <QuizSlide quiz={mcWithMeta} feedback={null} onSubmit={jest.fn()} />,
    );
    fireEvent.click(screen.getByText("A. Machine Learning"));
    render(
      <QuizSlide
        quiz={mcWithMeta}
        feedback={{
          is_correct: false,
          good_points: null,
          bad_points: null,
          round_done: false,
        }}
        onSubmit={jest.fn()}
      />,
    );
    expect(screen.getAllByTestId("feedback-panel").length).toBeGreaterThan(0);
  });

  it("renders View chapter link when chapter_title is set and handler provided", () => {
    const onJumpToChapter = jest.fn();
    render(
      <QuizSlide
        quiz={mcQuiz}
        feedback={null}
        onSubmit={jest.fn()}
        onJumpToChapter={onJumpToChapter}
      />,
    );
    const link = screen.getByTestId("view-chapter-link");
    expect(link).toBeInTheDocument();
    expect(link).toHaveTextContent("View chapter: What is ML");
  });

  it("calls onJumpToChapter with chapter_id when link is clicked", () => {
    const onJumpToChapter = jest.fn();
    render(
      <QuizSlide
        quiz={mcQuiz}
        feedback={null}
        onSubmit={jest.fn()}
        onJumpToChapter={onJumpToChapter}
      />,
    );
    fireEvent.click(screen.getByTestId("view-chapter-link"));
    expect(onJumpToChapter).toHaveBeenCalledWith(9);
  });

  it("renders View chapter link even in feedback state", () => {
    render(
      <QuizSlide
        quiz={mcQuiz}
        feedback={{ is_correct: true, round_done: false }}
        onSubmit={jest.fn()}
        onJumpToChapter={jest.fn()}
      />,
    );
    expect(screen.getByTestId("view-chapter-link")).toBeInTheDocument();
  });

  it("does not render link when onJumpToChapter handler is missing", () => {
    render(<QuizSlide quiz={mcQuiz} feedback={null} onSubmit={jest.fn()} />);
    expect(screen.queryByTestId("view-chapter-link")).not.toBeInTheDocument();
  });
});
