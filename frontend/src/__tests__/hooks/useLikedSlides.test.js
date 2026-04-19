import { renderHook, act } from "@testing-library/react";
import useLikedSlides from "../../hooks/useLikedSlides";
import apiService from "../../services/api";

jest.mock("../../services/api");

describe("useLikedSlides", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiService.listLikedQuizzes.mockResolvedValue({
      quiz_ids: [],
      chapter_ids: [],
    });
    apiService.likeQuiz.mockResolvedValue({ liked: true });
    apiService.unlikeQuiz.mockResolvedValue({ liked: false });
    apiService.likeChapter.mockResolvedValue({ liked: true });
    apiService.unlikeChapter.mockResolvedValue({ liked: false });
  });

  it("loads quiz and chapter IDs on mount", async () => {
    apiService.listLikedQuizzes.mockResolvedValue({
      quiz_ids: [7, 9],
      chapter_ids: [3, 5],
    });

    const { result } = renderHook(() => useLikedSlides());
    await act(async () => {});

    expect(apiService.listLikedQuizzes).toHaveBeenCalled();
    expect(result.current.isLiked("quiz", 7)).toBe(true);
    expect(result.current.isLiked("quiz", 8)).toBe(false);
    expect(result.current.isLiked("chapter", 3)).toBe(true);
    expect(result.current.isLiked("chapter", 4)).toBe(false);
  });

  it("toggleLike('quiz', id) calls likeQuiz and marks liked", async () => {
    const { result } = renderHook(() => useLikedSlides());
    await act(async () => {});

    await act(async () => {
      await result.current.toggleLike("quiz", 42);
    });

    expect(apiService.likeQuiz).toHaveBeenCalledWith(42);
    expect(result.current.isLiked("quiz", 42)).toBe(true);
  });

  it("toggleLike('chapter', id) calls likeChapter and marks liked", async () => {
    const { result } = renderHook(() => useLikedSlides());
    await act(async () => {});

    await act(async () => {
      await result.current.toggleLike("chapter", 16);
    });

    expect(apiService.likeChapter).toHaveBeenCalledWith(16);
    expect(result.current.isLiked("chapter", 16)).toBe(true);
  });

  it("toggleLike on liked quiz calls unlikeQuiz and clears liked", async () => {
    apiService.listLikedQuizzes.mockResolvedValue({
      quiz_ids: [42],
      chapter_ids: [],
    });

    const { result } = renderHook(() => useLikedSlides());
    await act(async () => {});
    expect(result.current.isLiked("quiz", 42)).toBe(true);

    await act(async () => {
      await result.current.toggleLike("quiz", 42);
    });

    expect(apiService.unlikeQuiz).toHaveBeenCalledWith(42);
    expect(result.current.isLiked("quiz", 42)).toBe(false);
  });

  it("toggleLike on liked chapter calls unlikeChapter and clears liked", async () => {
    apiService.listLikedQuizzes.mockResolvedValue({
      quiz_ids: [],
      chapter_ids: [16],
    });

    const { result } = renderHook(() => useLikedSlides());
    await act(async () => {});
    expect(result.current.isLiked("chapter", 16)).toBe(true);

    await act(async () => {
      await result.current.toggleLike("chapter", 16);
    });

    expect(apiService.unlikeChapter).toHaveBeenCalledWith(16);
    expect(result.current.isLiked("chapter", 16)).toBe(false);
  });

  it("rolls back optimistic update on quiz API error", async () => {
    apiService.likeQuiz.mockRejectedValue(new Error("network"));

    const { result } = renderHook(() => useLikedSlides());
    await act(async () => {});

    await act(async () => {
      await result.current.toggleLike("quiz", 42);
    });

    expect(result.current.isLiked("quiz", 42)).toBe(false);
  });

  it("rolls back optimistic update on chapter API error", async () => {
    apiService.likeChapter.mockRejectedValue(new Error("network"));

    const { result } = renderHook(() => useLikedSlides());
    await act(async () => {});

    await act(async () => {
      await result.current.toggleLike("chapter", 16);
    });

    expect(result.current.isLiked("chapter", 16)).toBe(false);
  });
});
