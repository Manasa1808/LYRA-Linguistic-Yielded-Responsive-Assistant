import sounddevice as sd
import numpy as np
import webrtcvad
import collections
import time

class AudioHandler:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.vad = webrtcvad.Vad(1)  # Reduced aggressiveness: 0-3, using 1 for better capture

    def listen_for_speech(self):
        """
        Capture speech using WebRTC VAD.
        Opens mic once, detects speech start/stop, collects frames,
        stops after 900ms silence, returns float32 numpy array @16kHz.
        Does NOT call Whisper - only captures audio.
        """
        # Frame size for VAD: 30ms at 16kHz = 480 samples
        frame_duration = 30  # ms
        frame_size = int(self.sample_rate * frame_duration / 1000)  # 480

        # Silence threshold: 900ms / 30ms = 30 consecutive non-speech frames
        silence_threshold = 30

        # Pre-speech buffer: collect 300ms before speech starts (10 frames)
        pre_speech_buffer_size = 10

        collected_frames = []
        speech_started = False
        silence_count = 0

        # Ring buffer to hold pre-speech audio
        pre_speech_buffer = collections.deque(maxlen=pre_speech_buffer_size)

        # Main buffer for incoming audio
        audio_buffer = collections.deque(maxlen=200)

        def callback(indata, frames, time_info, status):
            """Callback captures raw audio and converts to int16 PCM"""
            if status:
                print(f"[AUDIO] Status: {status}")
            # Convert float32 to int16 PCM (correct scaling)
            audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
            audio_buffer.append(audio_int16)

        # Start stream with correct configuration
        stream = sd.InputStream(
            callback=callback,
            channels=self.channels,
            samplerate=self.sample_rate,
            blocksize=frame_size,
            dtype='float32'
        )
        stream.start()

        print("[AUDIO] 🎤 Listening for speech...")

        try:
            # Wait for audio to start flowing
            time.sleep(0.1)

            while True:
                if len(audio_buffer) == 0:
                    time.sleep(0.01)
                    continue

                frame = audio_buffer.popleft()

                # Ensure frame is exactly frame_size
                if len(frame) != frame_size:
                    continue

                # Feed to VAD (requires bytes)
                is_speech = self.vad.is_speech(frame.tobytes(), self.sample_rate)

                if is_speech:
                    if not speech_started:
                        speech_started = True
                        print("[AUDIO] 🎤 Speech started")

                        # Add pre-speech buffer to capture beginning
                        for buffered_frame in pre_speech_buffer:
                            collected_frames.append(buffered_frame)
                        pre_speech_buffer.clear()

                    # Collect speech frame
                    collected_frames.append(frame)
                    silence_count = 0
                else:
                    if not speech_started:
                        # Before speech starts, keep frames in pre-buffer
                        pre_speech_buffer.append(frame)
                    else:
                        # After speech started, still collect silent frames
                        # This prevents cutting off word endings
                        collected_frames.append(frame)
                        silence_count += 1

                        if silence_count >= silence_threshold:
                            print("[AUDIO] 🔇 Silence > 900ms, stopping")
                            break

            # Stop stream
            stream.stop()
            stream.close()

            if not collected_frames:
                print("[AUDIO] ❌ No speech detected")
                return np.array([], dtype=np.float32)

            # Merge all frames into single array
            combined_int16 = np.concatenate(collected_frames)

            # Convert int16 PCM to float32 in range [-1.0, 1.0]
            audio_float32 = combined_int16.astype(np.float32) / 32768.0

            duration = len(audio_float32) / self.sample_rate
            print(f"[AUDIO] ✅ Captured {len(audio_float32)} samples ({duration:.2f}s)")

            return audio_float32

        except Exception as e:
            print(f"[AUDIO] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            stream.stop()
            stream.close()
            return np.array([], dtype=np.float32)