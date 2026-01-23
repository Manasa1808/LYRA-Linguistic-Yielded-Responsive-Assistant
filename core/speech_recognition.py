# core/speech_recognition.py
import torch
import whisper
import numpy as np
import librosa


class SpeechRecognizer:
    """
    Multilingual Whisper-based speech recognition with:
      - GPU acceleration (FP16)
      - Language detection (tiny)
      - Model routing (base/medium)
      - Language stability across conversations
    """

    def __init__(self):
        if not torch.cuda.is_available():
            raise SystemError("❌ CUDA not available – LYRA requires GPU for Whisper.")
        
        self.device = "cuda"
        self.sample_rate = 16000
        
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        
        print(f"[WHISPER] 🚀 GPU: {torch.cuda.get_device_name(0)}")
        
        # Load all three models on GPU
        print("[WHISPER] Loading tiny model on GPU...")
        self.models = {
            "tiny": whisper.load_model("tiny", device=self.device),
        }
        print("[WHISPER] ✅ Tiny loaded")
        
        print("[WHISPER] Loading base model on GPU...")
        self.models["base"] = whisper.load_model("base", device=self.device)
        print("[WHISPER] ✅ Base loaded")
        
        print("[WHISPER] Loading medium model on GPU...")
        self.models["medium"] = whisper.load_model("medium", device=self.device)
        print("[WHISPER] ✅ Medium loaded")
        
        print("[WHISPER] ✅ All models ready on GPU")
        
        # Language stabilization - remembers recent language for fluency
        self.recent_language = None
        self.language_consistency_count = 0

    def is_loaded(self):
        """Check if all models are loaded"""
        return len(self.models) == 3 and all(self.models.values())
    
    def set_preferred_language(self, language):
        """
        FORCE language lock when user manually switches.
        This OVERRIDES all detection until user switches again.
        """
        if language in ['en', 'hi', 'kn']:
            self.recent_language = language
            self.language_consistency_count = 100  # FORCE LOCK (was 5)
            print(f"[WHISPER] 🔒 LOCKED to {language} - will ignore detection")
        else:
            print(f"[WHISPER] ⚠️ Invalid language: {language}")

    def transcribe(self, audio_data, language=None):
        """
        Transcribe audio with language stability for natural conversation flow.
        
        Pipeline:
        1. Clean audio → 16kHz float32
        2. Detect language with tiny (ALWAYS)
        3. Stabilize language across conversation
        4. Select model (base for English, medium for Indic)
        5. Transcribe with native script
        """
        try:
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Clean and prepare audio
            # ═══════════════════════════════════════════════════════════
            
            if isinstance(audio_data, torch.Tensor):
                audio_data = audio_data.detach().cpu().numpy()
            
            audio_data = np.asarray(audio_data, dtype=np.float32).flatten()

            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=-1)

            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val

            duration = len(audio_data) / self.sample_rate
            if duration < 0.8:
                return {
                    "text": "",
                    "language": self.recent_language or "en",
                    "confidence": 0.0,
                    "model": "too_short"
                }

            # ═══════════════════════════════════════════════════════════
            # STEP 2: Detect language with tiny model
            # ═══════════════════════════════════════════════════════════
            
            audio_for_detection = whisper.pad_or_trim(audio_data)
            mel = whisper.log_mel_spectrogram(audio_for_detection).to(self.device)
            
            with torch.no_grad():
                _, probs = self.models["tiny"].detect_language(mel)
            
            detected_lang = max(probs, key=probs.get)
            raw_confidence = probs[detected_lang]
            
            # ═══════════════════════════════════════════════════════════
            # STEP 3: Map and stabilize language
            # ═══════════════════════════════════════════════════════════
            
            # Map similar Indic languages to supported ones
            lang_map = {
                'gu': 'hi', 'mr': 'hi', 'te': 'hi', 'ta': 'hi',
                'pa': 'hi', 'bn': 'hi', 'ur': 'hi', 'or': 'hi',
                'ml': 'hi', 'as': 'hi', 'sd': 'hi',
                'kn': 'kn', 'hi': 'hi', 'en': 'en'
            }
            
            mapped_lang = lang_map.get(detected_lang, 'en')
            
            # Language stabilization for conversation fluency
            confidence = raw_confidence
            
            # ✅ FORCE LOCK: If language was manually set, ALWAYS use it
            if self.language_consistency_count >= 100:
                # Language is LOCKED - ignore detection completely
                lang = self.recent_language
                confidence = 0.9  # High confidence for locked language
                if detected_lang != lang:
                    print(f"[WHISPER] 🔒 LOCKED {lang} (ignored {detected_lang})")
            elif confidence < 0.45:
                # Low confidence - use recent language if available
                if self.recent_language:
                    lang = self.recent_language
                    confidence = 0.5
                    print(f"[WHISPER] 🔄 Stabilized: {detected_lang}({raw_confidence:.2f}) → {lang}")
                else:
                    lang = mapped_lang
            else:
                # High confidence - accept detection
                lang = mapped_lang
                
                # Track consistency (but don't override locked language)
                if self.language_consistency_count < 100:
                    if lang == self.recent_language:
                        self.language_consistency_count += 1
                    else:
                        self.language_consistency_count = 1
                        self.recent_language = lang
                
                print(f"[WHISPER] 🌍 {lang} (conf: {confidence:.2f}, streak: {self.language_consistency_count})")
            
            # Adaptive confidence threshold based on language stability
            min_conf = 0.18 if self.language_consistency_count >= 3 else 0.22
            
            if confidence < min_conf:
                return {
                    "text": "",
                    "language": lang,
                    "confidence": confidence,
                    "model": "low_confidence"
                }

            # ═══════════════════════════════════════════════════════════
            # STEP 4: Select model based on language (FORCE MEDIUM FOR LOCKED INDIC)
            # ═══════════════════════════════════════════════════════════
            
            # ✅ FORCE MEDIUM: If Kannada/Hindi is LOCKED, always use medium
            if lang in ['kn', 'hi']:
                model_name = "medium"
                model = self.models["medium"]
            elif duration < 5.0:
                model_name = "base"
                model = self.models["base"]
            else:
                model_name = "medium"
                model = self.models["medium"]

            # ═══════════════════════════════════════════════════════════
            # STEP 5: Transcribe with native script
            # ═══════════════════════════════════════════════════════════
            
            transcribe_params = {
                "fp16": True,
                "language": lang,
                "verbose": False,
                "condition_on_previous_text": False,
                "no_speech_threshold": 0.6,
                "logprob_threshold": -1.0,
                "compression_ratio_threshold": 2.4,
            }
            
            # Force native script for Indic languages
            if lang in ['kn', 'hi']:
                transcribe_params["task"] = "transcribe"
            
            result = model.transcribe(audio_data, **transcribe_params)
            text = result.get("text", "").strip()
            
            if text:
                print(f"[WHISPER] ✅ '{text}' [{model_name}]")
            
            return {
                "text": text,
                "language": lang,
                "confidence": confidence,
                "model": model_name
            }

        except Exception as e:
            print(f"[WHISPER] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "text": "",
                "language": self.recent_language or "en",
                "confidence": 0.0,
                "model": "error"
            }