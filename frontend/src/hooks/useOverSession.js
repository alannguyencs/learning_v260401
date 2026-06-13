import { useCallback, useEffect, useRef, useState } from "react";
import apiService from "../services/api";
import { createLiveTranscriber } from "../utils/liveTranscriber";

// Convert a chunk of 24 kHz Int16 PCM (ArrayBuffer) into Float32 samples for
// the playback worklet.
function int16BufferToFloat32(arrayBuffer) {
  const int16 = new Int16Array(arrayBuffer);
  const f32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i += 1) {
    const v = int16[i];
    f32[i] = v < 0 ? v / 0x8000 : v / 0x7fff;
  }
  return f32;
}

const EMPTY_REFS = {
  ws: null,
  captureCtx: null,
  playbackCtx: null,
  stream: null,
  capture: null,
  playback: null,
  micSource: null,
  turnActive: false,
  // Drop-late-frames gate: true while NOT in a live turn (after turn_complete /
  // interrupt, and while a fresh turn warms up). Cleared once the mic arms.
  awaitingSessionReady: false,
  // Arm-on-session-ready gate: true ONLY after an activity_start was sent, so a
  // stray session_ready while merely sitting on "between" can't auto-arm.
  pendingTurnStart: false,
};

// Press-to-talk ("Over Mode") voice session. Connects to /api/voice/v2v-over;
// server VAD is disabled and the user drives turn boundaries explicitly. Lazy
// open: the backend opens a fresh per-turn Gemini session only AFTER it receives
// the turn's activity_start, so no session is held open while the user reads /
// thinks between turns. The mic therefore arms on session_ready, not on click.
//   startTurn() — open the WebSocket on the first call; otherwise send
//                 activity_start. Either way the mic arms when session_ready
//                 arrives (state "connecting" until then).
//   endTurn()   — send activity_end ("I'm done — your turn").
//   interrupt() — flush playback + abort mid-reply, then wait on "between".
//   stop()      — tear the session down.
// state: "idle" | "connecting" | "recording" | "speaking" | "between"
//        | "stopping" | "denied" | "error"
export function useOverSession({ voice, onEvent, onError }) {
  const [state, setState] = useState("idle");
  const [error, setError] = useState(null);
  const refs = useRef({ ...EMPTY_REFS });
  const transcriberRef = useRef(null);

  const cleanup = useCallback(() => {
    const r = refs.current;
    const safe = (fn) => {
      try {
        fn();
      } catch {
        /* ignore */
      }
    };
    safe(() => transcriberRef.current && transcriberRef.current.stop());
    safe(() => r.ws && r.ws.readyState <= 1 && r.ws.close(1000, "client stop"));
    safe(() => r.micSource && r.micSource.disconnect());
    safe(() => r.capture && r.capture.disconnect());
    safe(() => r.playback && r.playback.disconnect());
    safe(() => r.stream && r.stream.getTracks().forEach((t) => t.stop()));
    safe(
      () =>
        r.captureCtx && r.captureCtx.state !== "closed" && r.captureCtx.close(),
    );
    safe(
      () =>
        r.playbackCtx &&
        r.playbackCtx.state !== "closed" &&
        r.playbackCtx.close(),
    );
    refs.current = { ...EMPTY_REFS };
  }, []);

  const stop = useCallback(() => {
    setState("stopping");
    cleanup();
    setState("idle");
  }, [cleanup]);

  const sendControl = useCallback((type) => {
    const { ws } = refs.current;
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type }));
  }, []);

  const startTranscription = useCallback(() => {
    if (!transcriberRef.current) {
      transcriberRef.current = createLiveTranscriber();
    }
    if (transcriberRef.current) {
      transcriberRef.current.start((text) => {
        if (onEvent) onEvent({ type: "input_transcript_live", text });
      });
    }
  }, [onEvent]);

  const stopTranscription = useCallback(() => {
    if (transcriberRef.current) transcriberRef.current.stop();
  }, []);

  const handleMessage = useCallback(
    (event, ws, playback, beginRecordingTurn) => {
      if (event.data instanceof ArrayBuffer) {
        if (refs.current.awaitingSessionReady) return; // drop late audio
        const samples = int16BufferToFloat32(event.data);
        playback.port.postMessage({ type: "push", samples }, [samples.buffer]);
        return;
      }
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }
      if (msg.type === "turn_complete") {
        refs.current.turnActive = false;
        stopTranscription();
        refs.current.awaitingSessionReady = true;
        refs.current.pendingTurnStart = false;
        setState("between");
      } else if (msg.type === "session_ready") {
        if (refs.current.pendingTurnStart) beginRecordingTurn();
      }
      const suppressed =
        refs.current.awaitingSessionReady &&
        (msg.type === "output_transcript" || msg.type === "input_transcript");
      if (onEvent && !suppressed) onEvent(msg);
    },
    [onEvent, stopTranscription],
  );

  const openSession = useCallback(async () => {
    setState("connecting");
    setError(null);
    let captureCtx = null;
    let playbackCtx = null;
    let stream = null;
    try {
      const Ctor = window.AudioContext || window.webkitAudioContext;
      captureCtx = new Ctor();
      playbackCtx = new Ctor({ sampleRate: 24000 });
      await captureCtx.audioWorklet.addModule(
        "/worklets/mic-capture-worklet.js",
      );
      await playbackCtx.audioWorklet.addModule("/worklets/playback-worklet.js");

      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      if (captureCtx.state === "suspended") await captureCtx.resume();

      const capture = new AudioWorkletNode(captureCtx, "mic-capture");
      const playback = new AudioWorkletNode(playbackCtx, "playback");
      const micSource = captureCtx.createMediaStreamSource(stream);
      micSource.connect(capture);
      // Route capture → muted gain → destination so the worklet keeps firing
      // process() even while the user is silent.
      const mute = captureCtx.createGain();
      mute.gain.value = 0;
      capture.connect(mute);
      mute.connect(captureCtx.destination);
      playback.connect(playbackCtx.destination);

      const ws = new WebSocket(apiService.voiceWsUrl(voice || "Kore"));
      ws.binaryType = "arraybuffer";

      capture.port.onmessage = (e) => {
        if (!e.data) return;
        if (refs.current.turnActive && ws.readyState === 1) ws.send(e.data);
      };

      const beginRecordingTurn = () => {
        refs.current.pendingTurnStart = false;
        refs.current.awaitingSessionReady = false;
        refs.current.turnActive = true;
        startTranscription();
        setState("recording");
      };

      ws.onopen = () => {
        refs.current.pendingTurnStart = true;
        refs.current.awaitingSessionReady = true;
        ws.send(JSON.stringify({ type: "activity_start" }));
        setState("connecting");
      };
      ws.onmessage = (event) =>
        handleMessage(event, ws, playback, beginRecordingTurn);
      ws.onerror = () => {
        if (onError) onError("WebSocket error");
        setError("WebSocket error");
        setState("error");
        cleanup();
      };
      ws.onclose = (ev) => {
        if (ev.code !== 1000) {
          const reason = ev.reason || `code ${ev.code}`;
          if (onError) onError(`Voice session closed: ${reason}`);
          setError(reason);
          setState("error");
        } else {
          setState("idle");
        }
        cleanup();
      };

      refs.current = {
        ws,
        captureCtx,
        playbackCtx,
        stream,
        capture,
        playback,
        micSource,
        turnActive: false,
        awaitingSessionReady: false,
        pendingTurnStart: false,
      };
    } catch (err) {
      for (const ctx of [captureCtx, playbackCtx]) {
        if (ctx && ctx.state !== "closed") {
          try {
            ctx.close();
          } catch {
            /* ignore */
          }
        }
      }
      if (stream) {
        try {
          stream.getTracks().forEach((t) => t.stop());
        } catch {
          /* ignore */
        }
      }
      setState(err && err.name === "NotAllowedError" ? "denied" : "error");
      const msg = err?.message || String(err);
      setError(msg);
      if (onError) onError(msg);
    }
  }, [voice, onError, cleanup, startTranscription, handleMessage]);

  const startTurn = useCallback(() => {
    if (state === "connecting" || state === "recording") return;
    if (!refs.current.ws) {
      openSession();
      return;
    }
    refs.current.pendingTurnStart = true;
    refs.current.awaitingSessionReady = true;
    sendControl("activity_start");
    setState("connecting");
  }, [state, openSession, sendControl]);

  const endTurn = useCallback(() => {
    if (state !== "recording") return;
    refs.current.turnActive = false;
    sendControl("activity_end");
    stopTranscription();
    setState("speaking");
  }, [state, sendControl, stopTranscription]);

  const interrupt = useCallback(() => {
    if (state !== "speaking") return;
    const { playback } = refs.current;
    if (playback) playback.port.postMessage({ type: "flush" });
    refs.current.turnActive = false;
    // A dedicated interrupt frame aborts the in-progress generation
    // (activity_end would NOT — it only marks the user's turn finished).
    sendControl("interrupt");
    if (onEvent) onEvent({ type: "turn_reset" });
    refs.current.awaitingSessionReady = true;
    refs.current.pendingTurnStart = false;
    setState("between");
  }, [state, sendControl, onEvent]);

  useEffect(() => () => cleanup(), [cleanup]);

  return { state, error, startTurn, endTurn, interrupt, stop };
}
