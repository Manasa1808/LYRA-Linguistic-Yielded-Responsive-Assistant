# core/audio_handler.py
import sounddevice as sd
import numpy as np
import webrtcvad
import queue
import threading
import time
import sys
import torch

class AudioHandler:
    """
    Handles real-time microphone input with WebRTC VAD (Voice Activity Detection)
    to automatically start/stop recording when user speaks.
    """

    def __init__(self, sample_rate=16000, channels=1, aggressiveness=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.vad = webrtcvad.Vad(aggressiveness)
        self.chunk_duration = 30  # ms per frame for VAD
        self.chunk_size = int(sample_rate * self.chunk_duration / 1000)
        self.buffer_queue = queue.Queue()
        self.listening = False
        self.recording_thread = None
        self.stop_event = threading.Event()

    def start_listening(self):
        """Starts the continuous recording thread safely."""
        if self.listening:
            print("[LYRA] 🎧 Microphone is already active.")
            return

        print("[LYRA] 🎤 Starting continuous microphone listening thread...")
        self.stop_event.clear()
        self.listening = True
        self.recording_thread = threading.Thread(target=self._record_stream, daemon=True)
        self.recording_thread.start()
    
    def _normalize_audio(self, audio):
        """Normalize audio to float32 range"""
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32) / np.max(np.abs(audio))
        return audio

    def _frame_generator(self, audio):
        """Yields PCM frames for VAD processing"""
        bytes_per_sample = 2
        for i in range(0, len(audio), self.chunk_size):
            yield audio[i:i + self.chunk_size].tobytes()

    def _is_speech(self, frame_bytes):
        """Check if a given PCM frame contains speech"""
        try:
            return self.vad.is_speech(frame_bytes, self.sample_rate)
        except Exception:
            return False

    def _record_stream(self):
        """Continuously captures mic input and segments full speech utterances."""
        print("[LYRA] 🎤 Continuous microphone listening started...")
        silence_threshold = 1.2  # seconds of silence before stopping
        min_speech_duration = 0.8  # must be longer than 0.8s
        silence_start = None
        speaking = False
        current_audio = []

        while not self.stop_event.is_set():
            try:
                with sd.InputStream(samplerate=self.sample_rate,
                                    channels=self.channels,
                                    dtype='int16',
                                    blocksize=self.chunk_size) as stream:
                    print(f"[LYRA] 🎧 Mic active at {self.sample_rate} Hz")

                    while not self.stop_event.is_set():
                        block, _ = stream.read(self.chunk_size)
                        frame_bytes = block.tobytes()
                        is_speech = self._is_speech(frame_bytes)

                        if is_speech:
                            current_audio.append(block.copy())
                            silence_start = None
                            if not speaking:
                                print("[LYRA] 🎙️ Detected voice start")
                                speaking = True
                        else:
                            if speaking:
                                if silence_start is None:
                                    silence_start = time.time()
                                elif time.time() - silence_start >= silence_threshold:
                                    # End of utterance detected
                                    print("[LYRA] 🔇 Voice end detected")
                                    if len(current_audio) == 0:
                                        speaking = False
                                        continue

                                    full_audio = np.concatenate(current_audio, axis=0)
                                    current_audio = []
                                    speaking = False

                                    # Convert to float32 mono
                                    audio_np = full_audio.astype(np.float32).flatten() / 32768.0
                                    audio_np = np.clip(audio_np, -1.0, 1.0)
                                    if audio_np.ndim > 1:
                                        audio_np = np.mean(audio_np, axis=-1)
                                    # ✅ Guarantee 16kHz mono normalized float
                                    audio_np = np.ascontiguousarray(audio_np, dtype=np.float32)
                                    duration = len(audio_np) / self.sample_rate

                                    if duration >= min_speech_duration:
                                        print(f"[LYRA] 🎧 Captured segment: {duration:.2f}s ({len(audio_np)} samples)")
                                        self.buffer_queue.put(audio_np)
                                    else:
                                        print(f"[LYRA] ⚠️ Discarded short segment ({duration:.2f}s)")

                # end stream loop
            except Exception as mic_err:
                print(f"[LYRA] ⚠️ Microphone stream error: {mic_err}")
                print("[LYRA] 🔁 Restarting microphone stream in 2s...")
                time.sleep(2)
                continue

        print("[LYRA] 🛑 Microphone stopped")



    def start_continuous_recording(self, callback=None, chunk_duration=None):
        """Start background microphone thread. 
           Backward compatible: accepts optional 'callback' and 'chunk_duration' (ignored for now)
        """
        if self.listening:
            return
        self.stop_event.clear()
        self.listening = True
        self.recording_thread = threading.Thread(target=self._record_stream, daemon=True)
        self.recording_thread.start()

    def stop_continuous_recording(self):
        """Stop background recording thread"""
        self.stop_event.set()
        self.listening = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2)
            self.recording_thread = None

    def get_next_audio_segment(self, timeout=10):
        """Retrieve the next completed speech segment"""
        try:
            segment = self.buffer_queue.get(timeout=timeout)
            return self._normalize_audio(segment)
        except queue.Empty:
            return None

    def record_audio(self, duration=5, apply_filters=False):
        """Backward compatible recording function.
        'apply_filters' is accepted but ignored for compatibility."""
        print(f"[LYRA] 🎧 Recording fixed {duration}s audio... (filters={'on' if apply_filters else 'off'})")
        audio = sd.rec(int(duration * self.sample_rate),
                   samplerate=self.sample_rate,
                   channels=self.channels,
                   dtype='float32')
        sd.wait()
        return audio.flatten()

    def detect_voice_activity(self, audio_data, threshold=0.008, min_duration=0.15):
        """Used by main.py — lightweight VAD"""
        energy = np.mean(np.abs(audio_data))
        return energy > threshold and len(audio_data) / self.sample_rate > min_duration
