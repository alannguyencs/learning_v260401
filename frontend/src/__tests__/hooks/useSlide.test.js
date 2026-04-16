import { renderHook, waitFor, act } from "@testing-library/react";
import useSlide from "../../hooks/useSlide";
import apiService from "../../services/api";

jest.mock("../../services/api");

describe("useSlide", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads current slide on mount", async () => {
    const mockSlide = {
      slide_type: "chapter",
      chapter: { id: 1, title: "Intro" },
      quiz: null,
      has_previous: false,
      feedback: null,
    };
    apiService.getCurrentSlide.mockResolvedValue(mockSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.slide).toEqual(mockSlide);
    expect(result.current.hasPrevious).toBe(false);
    expect(result.current.feedback).toBeNull();
  });

  it("sets hasPrevious from response", async () => {
    const mockSlide = {
      slide_type: "quiz",
      chapter: null,
      quiz: { id: 5, question: "What is ML?" },
      has_previous: true,
      feedback: null,
    };
    apiService.getCurrentSlide.mockResolvedValue(mockSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.hasPrevious).toBe(true);
  });

  it("sets feedback from response when replaying history", async () => {
    const mockSlide = {
      slide_type: "quiz",
      chapter: null,
      quiz: { id: 5, question: "Q?" },
      has_previous: true,
      feedback: { is_correct: true, good_points: ["Good"], bad_points: [] },
    };
    apiService.getCurrentSlide.mockResolvedValue(mockSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.feedback).toEqual(mockSlide.feedback);
  });

  it("markLearnt calls slideForward with mark_chapter_id", async () => {
    const firstSlide = {
      slide_type: "chapter",
      chapter: { id: 1, title: "Chapter 1" },
      quiz: null,
      has_previous: false,
      feedback: null,
    };
    const secondSlide = {
      slide_type: "quiz",
      chapter: null,
      quiz: { id: 5, question: "Q?" },
      has_previous: true,
      feedback: null,
    };
    apiService.getCurrentSlide.mockResolvedValue(firstSlide);
    apiService.slideForward.mockResolvedValue(secondSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.markLearnt(1);
    });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(apiService.slideForward).toHaveBeenCalledWith(
      expect.objectContaining({ mark_chapter_id: 1 }),
    );
    expect(result.current.slide.slide_type).toBe("quiz");
    expect(result.current.hasPrevious).toBe(true);
  });

  it("goPrevious calls slideBack and updates state", async () => {
    const currentSlide = {
      slide_type: "quiz",
      chapter: null,
      quiz: { id: 5 },
      has_previous: true,
      feedback: null,
    };
    const prevSlide = {
      slide_type: "chapter",
      chapter: { id: 1, title: "Ch1" },
      quiz: null,
      has_previous: false,
      feedback: null,
    };
    apiService.getCurrentSlide.mockResolvedValue(currentSlide);
    apiService.slideBack.mockResolvedValue(prevSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.goPrevious();
    });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(apiService.slideBack).toHaveBeenCalled();
    expect(result.current.slide.slide_type).toBe("chapter");
    expect(result.current.hasPrevious).toBe(false);
  });

  it("fetchNextSlide without arg sends book_id from state", async () => {
    const mockSlide = {
      slide_type: "chapter",
      chapter: { id: 1, title: "Ch1" },
      quiz: null,
      has_previous: false,
      feedback: null,
    };
    const nextSlide = {
      slide_type: "quiz",
      chapter: null,
      quiz: { id: 5, question: "Q?" },
      has_previous: true,
      feedback: null,
    };
    apiService.getCurrentSlide.mockResolvedValue(mockSlide);
    apiService.slideForward.mockResolvedValue(nextSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.fetchNextSlide();
    });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(apiService.slideForward).toHaveBeenCalledWith({ book_id: null });
  });

  it("fetchNextSlide with chapterId sends mark_chapter_id", async () => {
    const mockSlide = {
      slide_type: "chapter",
      chapter: { id: 1, title: "Ch1" },
      quiz: null,
      has_previous: false,
      feedback: null,
    };
    const nextSlide = {
      slide_type: "quiz",
      chapter: null,
      quiz: { id: 5, question: "Q?" },
      has_previous: true,
      feedback: null,
    };
    apiService.getCurrentSlide.mockResolvedValue(mockSlide);
    apiService.slideForward.mockResolvedValue(nextSlide);

    const { result } = renderHook(() => useSlide());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.fetchNextSlide(42);
    });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(apiService.slideForward).toHaveBeenCalledWith({
      book_id: null,
      mark_chapter_id: 42,
    });
  });

  it("submitAnswer stores feedback without advancing slide", async () => {
    const mockSlide = {
      slide_type: "quiz",
      quiz: { id: 5, question: "Q?" },
      chapter: null,
      has_previous: false,
      feedback: null,
    };
    const mockFeedback = {
      is_correct: true,
      good_points: ["Good"],
      bad_points: [],
      round_done: false,
    };
    apiService.getCurrentSlide.mockResolvedValue(mockSlide);
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
