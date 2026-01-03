## 3. Fixed Audio Handler

import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy import signal
import queue
import threading
from config import SAMPLE_RATE, CHANNELS

class AudioHandler:
    def __init__(self, sample_rate=SAMPLE_RATE, channels=CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
        self.recording_data = []
        
    def noise_reduction(self, audio_data, strength=0.5):
        """Simple spectral subtraction for noise reduction"""
        try:
            # Ensure audio is 1D
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            # Convert to frequency domain
            fft = np.fft.rfft(audio_data)
            magnitude = np.abs(fft)
            phase = np.angle(fft)
            
            # Estimate noise profile from first 0.5 seconds
            noise_samples = min(int(0.5 * self.sample_rate), len(magnitude) // 4)
            if noise_samples > 0:
                noise_profile = np.mean(magnitude[:noise_samples])
            else:
                noise_profile = np.mean(magnitude) * 0.1
            
            # Subtract noise
            magnitude_cleaned = magnitude - (noise_profile * strength)
            magnitude_cleaned = np.maximum(magnitude_cleaned, 0)
            
            # Reconstruct signal
            fft_cleaned = magnitude_cleaned * np.exp(1j * phase)
            audio_cleaned = np.fft.irfft(fft_cleaned, n=len(audio_data))
            
            return audio_cleaned
        except Exception as e:
            print(f"Noise reduction error: {e}")
            return audio_data
    
    def apply_bandpass_filter(self, audio_data, lowcut=80, highcut=3400):
        """Apply bandpass filter for human voice frequency range"""
        try:
            # Ensure audio is 1D
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()

            nyquist = 0.5 * self.sample_rate
            low = lowcut / nyquist
            high = highcut / nyquist

            # Ensure valid frequency range
            low = max(0.01, min(low, 0.99))
            high = max(0.01, min(high, 0.99))

            if low >= high:
                return audio_data

            b, a = signal.butter(4, [low, high], btype='band')
            filtered = signal.filtfilt(b, a, audio_data)
            return filtered
        except Exception as e:
            print(f"Bandpass filter error: {e}")
            return audio_data

    def detect_voice_activity(self, audio_data, threshold=0.01, min_duration=0.5):
        """Simple voice activity detection using energy threshold"""
        try:
            # Ensure audio is 1D
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()

            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_data**2))

            # Check if energy is above threshold
            if rms > threshold:
                # Additional check: ensure minimum duration of speech-like activity
                # Look for sustained energy above a lower threshold
                window_size = int(min_duration * self.sample_rate)
                if len(audio_data) >= window_size:
                    # Calculate rolling RMS
                    rolling_rms = []
                    for i in range(0, len(audio_data) - window_size, window_size // 4):
                        window = audio_data[i:i + window_size]
                        window_rms = np.sqrt(np.mean(window**2))
                        rolling_rms.append(window_rms)

                    # Check if at least half the windows have sufficient energy
                    active_windows = sum(1 for r in rolling_rms if r > threshold * 0.5)
                    if active_windows >= len(rolling_rms) * 0.5:
                        return True

            return False
        except Exception as e:
            print(f"Voice activity detection error: {e}")
            return False
    
    def record_audio(self, duration=5, apply_filters=True):
        """Record audio for specified duration"""
        print(f"🎤 Recording for {duration} seconds...")
        
        try:
            # Record audio
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32'
            )
            sd.wait()
            
            # Flatten if stereo
            if len(audio.shape) > 1:
                audio = audio.flatten()
            
            # Apply filters
            if apply_filters:
                print("🔄 Applying filters...")
                audio = self.apply_bandpass_filter(audio)
                audio = self.noise_reduction(audio)
            
            print("✅ Recording complete")
            return audio
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return np.array([])
    
    def start_continuous_recording(self, callback, chunk_duration=3):
        """Start continuous audio recording with callback"""
        self.is_recording = True
        self.recording_data = []
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            if self.is_recording:
                # Copy and flatten the data
                data_copy = indata.copy()
                if len(data_copy.shape) > 1:
                    data_copy = data_copy.flatten()
                self.audio_queue.put(data_copy)
        
        # Start audio stream
        try:
            self.stream = sd.InputStream(
                callback=audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * 0.1),  # 100ms blocks
                dtype='float32'
            )
            self.stream.start()
            print("🎤 Continuous recording started")
        except Exception as e:
            print(f"❌ Failed to start stream: {e}")
            self.is_recording = False
            return
        
        # Processing thread
        def process_audio():
            buffer = []
            chunks_needed = int(chunk_duration / 0.1)  # Number of 100ms chunks for desired duration
            
            while self.is_recording:
                try:
                    chunk = self.audio_queue.get(timeout=0.5)
                    buffer.append(chunk)
                    
                    # Process when buffer reaches desired duration
                    if len(buffer) >= chunks_needed:
                        audio_data = np.concatenate(buffer)
                        
                        # Apply filters
                        audio_data = self.apply_bandpass_filter(audio_data)
                        audio_data = self.noise_reduction(audio_data)
                        
                        # Call the callback with processed audio
                        try:
                            callback(audio_data)
                        except Exception as e:
                            print(f"Callback error: {e}")
                        
                        buffer = []
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Processing error: {e}")
                    continue
        
        self.processing_thread = threading.Thread(target=process_audio, daemon=True)
        self.processing_thread.start()
    
    def stop_continuous_recording(self):
        """Stop continuous recording"""
        print("🛑 Stopping continuous recording...")
        self.is_recording = False
        
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
        
        print("✅ Recording stopped")
    
    def play_audio(self, audio_data, sample_rate=None):
        """Play audio data"""
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            # Ensure audio is the right format
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            # Normalize audio
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            sd.play(audio_data, sample_rate)
            sd.wait()
        except Exception as e:
            print(f"❌ Playback error: {e}")
    
    def save_audio(self, audio_data, filename, sample_rate=None):
        """Save audio to file"""
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            sf.write(filename, audio_data, sample_rate)
            print(f"✅ Audio saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save audio: {e}")
    
    def load_audio(self, filename):
        """Load audio from file"""
        try:
            audio_data, sample_rate = sf.read(filename)
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                from scipy import signal as sp_signal
                num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
                audio_data = sp_signal.resample(audio_data, num_samples)
            
            print(f"✅ Audio loaded from {filename}")
            return audio_data
        except Exception as e:
            print(f"❌ Failed to load audio: {e}")
            return None