import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatButton from "../../components/ChatButton";
import ChatPanel from "../../components/ChatPanel";

jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);

jest.mock("../../hooks/useSlideChat", () => () => ({
  messages: [
    { role: "user", content: "Hello", created_at: "2026-04-02T10:00:00" },
    {
      role: "assistant",
      content: "Hi there!",
      created_at: "2026-04-02T10:00:01",
    },
  ],
  loading: false,
  sendMessage: jest.fn(),
}));

describe("ChatButton", () => {
  it("renders on chapter slide", () => {
    render(<ChatButton slideType="chapter" chapterId={1} quizId={null} />);
    expect(screen.getByLabelText("Open chat")).toBeInTheDocument();
  });

  it("renders on quiz slide", () => {
    render(<ChatButton slideType="quiz" chapterId={null} quizId={1} />);
    expect(screen.getByLabelText("Open chat")).toBeInTheDocument();
  });

  it("opens ChatPanel when clicked", () => {
    render(<ChatButton slideType="chapter" chapterId={1} quizId={null} />);
    fireEvent.click(screen.getByLabelText("Open chat"));
    expect(screen.getByText("Chat")).toBeInTheDocument();
  });
});

describe("ChatPanel", () => {
  it("displays message history", () => {
    render(
      <ChatPanel
        messages={[
          { role: "user", content: "Test Q", created_at: "2026-04-02T10:00:00" },
          {
            role: "assistant",
            content: "Test A",
            created_at: "2026-04-02T10:00:01",
          },
        ]}
        loading={false}
        onSend={jest.fn()}
        onClose={jest.fn()}
      />,
    );
    expect(screen.getByText("Test Q")).toBeInTheDocument();
    expect(screen.getByText("Test A")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    const onClose = jest.fn();
    render(
      <ChatPanel
        messages={[]}
        loading={false}
        onSend={jest.fn()}
        onClose={onClose}
      />,
    );
    fireEvent.click(screen.getByText("\u00d7"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onSend when form submitted", () => {
    const onSend = jest.fn();
    render(
      <ChatPanel
        messages={[]}
        loading={false}
        onSend={onSend}
        onClose={jest.fn()}
      />,
    );
    const input = screen.getByPlaceholderText("Ask a question...");
    fireEvent.change(input, { target: { value: "My question" } });
    fireEvent.submit(input.closest("form"));
    expect(onSend).toHaveBeenCalledWith("My question");
  });
});
