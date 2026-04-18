import { renderHook, act } from "@testing-library/react";
import useLikedQuizzes from "../../hooks/useLikedQuizzes";
import apiService from "../../services/api";

jest.mock("../../services/api");

describe("useLikedQuizzes", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiService.listLikedQuizzes.mockResolvedValue({ quiz_ids: [] });
    apiService.likeQuiz.mockResolvedValue({ liked: true });
    apiService.unlikeQuiz.mockResolvedValue({ liked: false });
  });

  it("loads liked IDs on mount", async () => {
    apiService.listLikedQuizzes.mockResolvedValue({ quiz_ids: [7, 9] });

    const { result } = renderHook(() => useLikedQuizzes());
    await act(async () => {});

    expect(apiService.listLikedQuizzes).toHaveBeenCalled();
    expect(result.current.isLiked(7)).toBe(true);
    expect(result.current.isLiked(9)).toBe(true);
    expect(result.current.isLiked(5)).toBe(false);
  });

  it("toggleLike on unliked quiz calls likeQuiz and marks liked", async () => {
    const { result } = renderHook(() => useLikedQuizzes());
    await act(async () => {});

    await act(async () => {
      await result.current.toggleLike(42);
    });

    expect(apiService.likeQuiz).toHaveBeenCalledWith(42);
    expect(result.current.isLiked(42)).toBe(true);
  });

  it("toggleLike on liked quiz calls unlikeQuiz and clears liked", async () => {
    apiService.listLikedQuizzes.mockResolvedValue({ quiz_ids: [42] });

    const { result } = renderHook(() => useLikedQuizzes());
    await act(async () => {});
    expect(result.current.isLiked(42)).toBe(true);

    await act(async () => {
      await result.current.toggleLike(42);
    });

    expect(apiService.unlikeQuiz).toHaveBeenCalledWith(42);
    expect(result.current.isLiked(42)).toBe(false);
  });

  it("rolls back optimistic update on API error", async () => {
    apiService.likeQuiz.mockRejectedValue(new Error("network"));

    const { result } = renderHook(() => useLikedQuizzes());
    await act(async () => {});

    await act(async () => {
      await result.current.toggleLike(42);
    });

    expect(result.current.isLiked(42)).toBe(false);
  });
});
