import { renderHook, act, waitFor } from "@testing-library/react";
import { useOverSession } from "../../hooks/useOverSession";
import apiService from "../../services/api";
import { createLiveTranscriber } from "../../utils/liveTranscriber";

jest.mock("../../services/api");
jest.mock("../../utils/liveTranscriber");

let lastWs = null;

class FakeWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 1; // OPEN
    this.sent = [];
    this.binaryType = "";
    lastWs = this;
  }

  send(data) {
    this.sent.push(data);
  }

  close(code = 1000, reason = "") {
    this.readyState = 3;
    if (this.onclose) this.onclose({ code, reason });
  }

  // Test helpers to drive server → client events.
  emit(obj) {
    if (this.onmessage) this.onmessage({ data: JSON.stringify(obj) });
  }
}

class FakeAudioContext {
  constructor() {
    this.state = "running";
    this.destination = {};
    this.audioWorklet = { addModule: jest.fn().mockResolvedValue(undefined) };
  }

  createMediaStreamSource() {
    return { connect: jest.fn(), disconnect: jest.fn() };
  }

  createGain() {
    return { gain: { value: 0 }, connect: jest.fn() };
  }

  resume() {
    return Promise.resolve();
  }

  close() {
    return Promise.resolve();
  }
}

class FakeWorkletNode {
  constructor() {
    this.port = { onmessage: null, postMessage: jest.fn() };
  }

  connect() {}

  disconnect() {}
}

function installAudioMocks(getUserMedia) {
  global.WebSocket = FakeWebSocket;
  global.AudioContext = FakeAudioContext;
  global.AudioWorkletNode = FakeWorkletNode;
  Object.defineProperty(global.navigator, "mediaDevices", {
    value: { getUserMedia },
    configurable: true,
  });
}

const okMedia = () =>
  Promise.resolve({ getTracks: () => [{ stop: jest.fn() }] });

describe("useOverSession", () => {
  beforeEach(() => {
    lastWs = null;
    jest.clearAllMocks();
    apiService.voiceWsUrl.mockReturnValue(
      "ws://test/api/voice/v2v-over?voice=Kore",
    );
    createLiveTranscriber.mockReturnValue(null);
  });

  it("starts idle", () => {
    installAudioMocks(okMedia);
    const { result } = renderHook(() => useOverSession({ voice: "Kore" }));
    expect(result.current.state).toBe("idle");
  });

  it("walks idle → connecting → recording → speaking → between → idle", async () => {
    installAudioMocks(okMedia);
    const { result } = renderHook(() => useOverSession({ voice: "Kore" }));

    await act(async () => {
      result.current.startTurn();
    });
    await waitFor(() => expect(lastWs).not.toBeNull());

    // ws opens → activity_start sent, connecting.
    act(() => lastWs.onopen());
    expect(result.current.state).toBe("connecting");
    expect(JSON.parse(lastWs.sent[0])).toEqual({ type: "activity_start" });

    // backend confirms session → mic arms.
    act(() => lastWs.emit({ type: "session_ready" }));
    expect(result.current.state).toBe("recording");

    // user finishes → activity_end, speaking.
    act(() => result.current.endTurn());
    expect(result.current.state).toBe("speaking");
    expect(JSON.parse(lastWs.sent[1])).toEqual({ type: "activity_end" });

    // model finishes → between.
    act(() => lastWs.emit({ type: "turn_complete" }));
    expect(result.current.state).toBe("between");

    // tear down.
    act(() => result.current.stop());
    expect(result.current.state).toBe("idle");
  });

  it("interrupt sends an interrupt frame and returns to between", async () => {
    installAudioMocks(okMedia);
    const { result } = renderHook(() => useOverSession({ voice: "Kore" }));

    await act(async () => {
      result.current.startTurn();
    });
    await waitFor(() => expect(lastWs).not.toBeNull());
    act(() => lastWs.onopen());
    act(() => lastWs.emit({ type: "session_ready" }));
    act(() => result.current.endTurn());

    act(() => result.current.interrupt());

    expect(result.current.state).toBe("between");
    expect(lastWs.sent.map((s) => JSON.parse(s).type)).toContain("interrupt");
  });

  it("denies when mic permission is blocked", async () => {
    const denied = () => {
      const err = new Error("blocked");
      err.name = "NotAllowedError";
      return Promise.reject(err);
    };
    installAudioMocks(denied);
    const onError = jest.fn();
    const { result } = renderHook(() =>
      useOverSession({ voice: "Kore", onError }),
    );

    await act(async () => {
      result.current.startTurn();
    });
    await waitFor(() => expect(result.current.state).toBe("denied"));
    expect(onError).toHaveBeenCalled();
  });
});
