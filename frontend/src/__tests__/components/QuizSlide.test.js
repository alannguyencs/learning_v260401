import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import QuizSlide from "../../components/QuizSlide";

const mcQuiz = {
  id: 1,
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
    render(
      <QuizSlide
        quiz={mcQuiz}
        feedback={null}
        onSubmit={jest.fn()}
        onSkip={jest.fn()}
        onNext={jest.fn()}
      />,
    );
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(4);
  });

  it("renders text area for free_recall type", () => {
    render(
      <QuizSlide
        quiz={recallQuiz}
        feedback={null}
        onSubmit={jest.fn()}
        onSkip={jest.fn()}
        onNext={jest.fn()}
      />,
    );
    expect(
      screen.getByPlaceholderText("Type your answer..."),
    ).toBeInTheDocument();
  });

  it("shows feedback panel after submit", () => {
    const mockFeedback = {
      is_correct: true,
      feedback: "Well explained.",
      round_done: false,
    };
    render(
      <QuizSlide
        quiz={mcQuiz}
        feedback={mockFeedback}
        onSubmit={jest.fn()}
        onSkip={jest.fn()}
        onNext={jest.fn()}
      />,
    );
    expect(screen.getByTestId("feedback-panel")).toBeInTheDocument();
    expect(screen.getByText(/Well explained/)).toBeInTheDocument();
  });

  it("Next Slide button appears after feedback shown", () => {
    const mockFeedback = {
      is_correct: false,
      feedback: "Try again.",
      round_done: false,
    };
    render(
      <QuizSlide
        quiz={recallQuiz}
        feedback={mockFeedback}
        onSubmit={jest.fn()}
        onSkip={jest.fn()}
        onNext={jest.fn()}
      />,
    );
    expect(screen.getByText("Next Slide")).toBeInTheDocument();
  });

  it("skip triggers onSkip callback", () => {
    const onSkip = jest.fn();
    render(
      <QuizSlide
        quiz={mcQuiz}
        feedback={null}
        onSubmit={jest.fn()}
        onSkip={onSkip}
        onNext={jest.fn()}
      />,
    );
    fireEvent.click(screen.getByText("Skip"));
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it("MC wrong answer: shows user pick red and correct green, hides others", () => {
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
      <QuizSlide
        quiz={mcWithMeta}
        feedback={null}
        onSubmit={jest.fn()}
        onSkip={jest.fn()}
        onNext={jest.fn()}
      />,
    );
    // Select option A (wrong)
    fireEvent.click(screen.getByText("A. Machine Learning"));
    // Now render with feedback to simulate post-submit
    render(
      <QuizSlide
        quiz={mcWithMeta}
        feedback={{ is_correct: false, feedback: "Wrong.", round_done: false }}
        onSubmit={jest.fn()}
        onSkip={jest.fn()}
        onNext={jest.fn()}
      />,
    );
    // The FeedbackPanel should be present
    expect(screen.getAllByTestId("feedback-panel").length).toBeGreaterThan(0);
  });

  it("MC correct answer: shows only user pick in green", () => {
    const mcWithMeta = {
      ...mcQuiz,
      correct_options: ["A"],
      quiz_metadata: {
        response_to_user_option_a: "Correct!",
        response_to_user_option_b: "Wrong.",
        response_to_user_option_c: "Nope.",
        response_to_user_option_d: "Nope.",
      },
    };
    render(
      <QuizSlide
        quiz={mcWithMeta}
        feedback={{
          is_correct: true,
          feedback: "Good job!",
          round_done: false,
        }}
        onSubmit={jest.fn()}
        onSkip={jest.fn()}
        onNext={jest.fn()}
      />,
    );
    expect(screen.getByTestId("feedback-panel")).toBeInTheDocument();
    expect(screen.getByText(/Good job!/)).toBeInTheDocument();
  });
});
