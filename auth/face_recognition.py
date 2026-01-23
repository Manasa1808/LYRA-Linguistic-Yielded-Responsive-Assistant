import cv2
import mediapipe as mp
import numpy as np
import pickle
import os
from pathlib import Path

class FaceRecognition:
    def __init__(self, encodings_dir="data/face_encodings"):
        self.encodings_dir = Path(encodings_dir)
        self.encodings_dir.mkdir(parents=True, exist_ok=True)
        
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)
        
        self.known_encodings = {}
        self.load_encodings()
    
    def extract_face_encoding(self, image):
        """Extract facial landmarks as encoding"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            encoding = []
            for landmark in landmarks.landmark:
                encoding.extend([landmark.x, landmark.y, landmark.z])
            return np.array(encoding)
        return None
    
    def register_user(self, username, num_samples=5):
        """Register a new user by capturing multiple face samples"""
        cap = cv2.VideoCapture(0)
        encodings = []
        samples_collected = 0
        
        print(f"Registering {username}. Please look at the camera.")
        
        while samples_collected < num_samples:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect face
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detection_results = self.face_detection.process(rgb_frame)
            
            if detection_results.detections:
                # Extract encoding
                encoding = self.extract_face_encoding(frame)
                if encoding is not None:
                    encodings.append(encoding)
                    samples_collected += 1
                    cv2.putText(frame, f"Sample {samples_collected}/{num_samples}", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Register Face', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if len(encodings) >= 3:
            # Average encodings
            avg_encoding = np.mean(encodings, axis=0)
            self.save_encoding(username, avg_encoding)
            return True, f"User {username} registered successfully"
        
        return False, "Not enough face samples collected"
    
    def save_encoding(self, username, encoding):
        """Save face encoding to file"""
        filepath = self.encodings_dir / f"{username}.pkl"
        with open(filepath, 'wb') as f:
            pickle.dump(encoding, f)
        self.known_encodings[username] = encoding
    
    def load_encodings(self):
        """Load all saved face encodings"""
        loaded_count = 0
        for filepath in self.encodings_dir.glob("*.pkl"):
            try:
                username = filepath.stem
                with open(filepath, 'rb') as f:
                    encoding = pickle.load(f)
                    self.known_encodings[username] = encoding
                    loaded_count += 1
                    print(f"✅ Loaded face encoding for: {username}")
            except Exception as e:
                print(f"⚠️ Error loading encoding from {filepath}: {e}")
        
        if loaded_count > 0:
            print(f"📚 Loaded {loaded_count} face encoding(s) from {self.encodings_dir}")
        else:
            print(f"ℹ️ No face encodings found in {self.encodings_dir}")
    
    def get_registered_users(self):
        """Get list of registered usernames"""
        return list(self.known_encodings.keys())
    
    def is_user_registered(self, username):
        """Check if a user is registered for face recognition"""
        return username in self.known_encodings
    
    def recognize_face(self, image, tolerance=0.6, distance_threshold=0.5):
        """Recognize face in image
        
        Args:
            image: Input image frame
            tolerance: Minimum similarity score (0-1)
            distance_threshold: Maximum allowed distance for match (lower = stricter)
        
        Returns:
            (username, confidence) tuple or (None, 0) if no match
        """
        encoding = self.extract_face_encoding(image)
        if encoding is None:
            return None, 0
        
        if not self.known_encodings:
            return None, 0
        
        best_match = None
        best_distance = float('inf')
        
        for username, known_encoding in self.known_encodings.items():
            # Calculate Euclidean distance between encodings
            distance = np.linalg.norm(encoding - known_encoding)
            if distance < best_distance:
                best_distance = distance
                best_match = username
        
        # Convert distance to similarity score (0-1 scale)
        # Lower distance = higher similarity
        # Using a normalized similarity: 1 / (1 + distance)
        similarity = 1 / (1 + best_distance)
        
        # Check both distance threshold and similarity threshold
        if best_distance <= distance_threshold and similarity >= tolerance:
            return best_match, similarity
        
        return None, 0
    
    def authenticate_user(self, timeout=15, distance_threshold=0.5):
        """Authenticate user via webcam
        
        Args:
            timeout: Maximum time to wait for authentication (seconds)
            distance_threshold: Maximum distance for face match (lower = stricter)
        
        Returns:
            (success: bool, username: str or None)
        """
        # Check if there are any registered users
        if not self.known_encodings:
            print("⚠️ No registered users found. Please register first.")
            return False, None
        
        print(f"📷 Starting face authentication... ({len(self.known_encodings)} registered user(s))")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera")
            return False, None
        
        start_time = cv2.getTickCount()
        frame_count = 0
        last_status_update = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Could not read frame from camera")
                break
            
            frame_count += 1
            
            # Check timeout
            elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            if elapsed > timeout:
                print(f"⏱️ Authentication timeout after {timeout} seconds")
                break
            
            # Try to recognize face
            username, confidence = self.recognize_face(frame, distance_threshold=distance_threshold)
            
            # Draw face detection box and status
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detection_results = self.face_detection.process(rgb_frame)
            
            # Draw detection box if face is detected
            if detection_results.detections:
                for detection in detection_results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = frame.shape
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    if username:
                        # Green box for recognized user
                        cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
                        cv2.putText(frame, f"Welcome {username} ({confidence:.2f})", 
                                  (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        # Yellow box for detected but not recognized
                        cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 255), 2)
                        cv2.putText(frame, "Face detected - Recognizing...", 
                                  (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                # No face detected
                cv2.putText(frame, "No face detected - Please look at the camera", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Show time remaining
            time_remaining = int(timeout - elapsed)
            cv2.putText(frame, f"Time remaining: {time_remaining}s", 
                      (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Show registered users count
            cv2.putText(frame, f"Registered users: {len(self.known_encodings)}", 
                      (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # If user recognized, wait a moment to confirm and return
            if username:
                # Show success message for a bit longer
                for _ in range(30):  # ~1 second at 30fps
                    ret, frame = cap.read()
                    if ret:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        detection_results = self.face_detection.process(rgb_frame)
                        if detection_results.detections:
                            for detection in detection_results.detections:
                                bbox = detection.location_data.relative_bounding_box
                                h, w, _ = frame.shape
                                x = int(bbox.xmin * w)
                                y = int(bbox.ymin * h)
                                width = int(bbox.width * w)
                                height = int(bbox.height * h)
                                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 3)
                                cv2.putText(frame, f"Welcome {username}!", 
                                          (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                        cv2.putText(frame, f"Confidence: {confidence:.2f}", 
                                  (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        cv2.imshow('Authentication', frame)
                        cv2.waitKey(33)  # ~30fps
                
                print(f"✅ Authentication successful: {username} (confidence: {confidence:.2f})")
                cap.release()
                cv2.destroyAllWindows()
                return True, username
            
            # Update status every second
            if int(elapsed) > last_status_update:
                last_status_update = int(elapsed)
                if detection_results.detections:
                    print(f"🔍 Face detected, recognizing... ({int(elapsed)}s)")
                else:
                    print(f"👁️ Looking for face... ({int(elapsed)}s)")
            
            cv2.imshow('Authentication', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("❌ Authentication cancelled by user")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("❌ Authentication failed - Face not recognized or timeout")
        return False, None