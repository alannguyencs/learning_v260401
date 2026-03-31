import { renderHook, waitFor, act } from "@testing-library/react";
import useSlide from "../../hooks/useSlide";
import apiService from "../../services/api";

jest.mock("../../services/api");

describe("useSlide", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetchNextSlide sets chapter slide state", async () => {
    const mockSlide = {
      slide_type: "chapter",
      chapter: { id: 1, title: "Intro" },
      quiz: null,
    };
    apiService.getNextSlide.mockResolvedValue(mockSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.slide).toEqual(mockSlide);
    expect(result.current.slide.slide_type).toBe("chapter");
  });

  it("fetchNextSlide sets quiz slide state", async () => {
    const mockSlide = {
      slide_type: "quiz",
      chapter: null,
      quiz: { id: 5, question: "What is ML?" },
    };
    apiService.getNextSlide.mockResolvedValue(mockSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.slide.slide_type).toBe("quiz");
  });

  it("fetchNextSlide sets allCaughtUp on none slide_type", async () => {
    const mockSlide = { slide_type: "none", chapter: null, quiz: null };
    apiService.getNextSlide.mockResolvedValue(mockSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.slide.slide_type).toBe("none");
  });

  it("after markLearnt, fetchNextSlide is called again", async () => {
    const firstSlide = {
      slide_type: "chapter",
      chapter: { id: 1, title: "Chapter 1" },
      quiz: null,
    };
    const secondSlide = {
      slide_type: "none",
      chapter: null,
      quiz: null,
    };
    apiService.getNextSlide
      .mockResolvedValueOnce(firstSlide)
      .mockResolvedValueOnce(secondSlide);
    apiService.markChapterLearnt.mockResolvedValue({
      lesson_fully_learnt: true,
    });

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.slide.slide_type).toBe("chapter");

    await act(async () => {
      await result.current.markLearnt(1);
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(apiService.markChapterLearnt).toHaveBeenCalledWith(1);
    expect(result.current.slide.slide_type).toBe("none");
  });

  it("submitAnswer stores feedback without advancing slide", async () => {
    const mockSlide = {
      slide_type: "quiz",
      quiz: { id: 5, question: "Q?" },
      chapter: null,
    };
    const mockFeedback = {
      is_correct: true,
      feedback: "Good.",
      round_done: false,
    };
    apiService.getNextSlide.mockResolvedValue(mockSlide);
    apiService.respondToQuiz.mockResolvedValue(mockFeedback);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.submitAnswer(5, {
        round_num: 0,
        lesson_id: 1,
        user_answer: "A",
        is_skip: false,
      });
    });

    expect(result.current.feedback).toEqual(mockFeedback);
    expect(result.current.slide.slide_type).toBe("quiz");
  });
});
