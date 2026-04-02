import { renderHook, act } from "@testing-library/react";
import useSlideChat from "../../hooks/useSlideChat";
import apiService from "../../services/api";

jest.mock("../../services/api");

describe("useSlideChat", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiService.getChatHistory.mockResolvedValue([]);
  });

  it("loads history on mount", async () => {
    const history = [
      { role: "user", content: "Q", created_at: "2026-04-02T10:00:00" },
    ];
    apiService.getChatHistory.mockResolvedValue(history);

    const { result } = renderHook(() => useSlideChat("chapter", 1, null));

    await act(async () => {});
    expect(apiService.getChatHistory).toHaveBeenCalledWith("chapter", 1, null);
    expect(result.current.messages).toEqual(history);
  });

  it("sendMessage calls API and updates messages", async () => {
    apiService.sendChatMessage.mockResolvedValue({ response: "Answer" });

    const { result } = renderHook(() => useSlideChat("chapter", 1, null));
    await act(async () => {});

    await act(async () => {
      await result.current.sendMessage("Question?");
    });

    expect(apiService.sendChatMessage).toHaveBeenCalledWith({
      slide_type: "chapter",
      chapter_id: 1,
      quiz_id: null,
      message: "Question?",
    });
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[1].role).toBe("assistant");
  });

  it("sets loading during API call", async () => {
    let resolvePromise;
    apiService.sendChatMessage.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );

    const { result } = renderHook(() => useSlideChat("chapter", 1, null));
    await act(async () => {});

    act(() => {
      result.current.sendMessage("Test");
    });
    expect(result.current.loading).toBe(true);

    await act(async () => {
      resolvePromise({ response: "Done" });
    });
    expect(result.current.loading).toBe(false);
  });
});
