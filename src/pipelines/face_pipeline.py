

import dlib
import numpy as np
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_all_students


@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector() 


    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec

import cv2

def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models()
    
    # Preprocess image to improve face detection under variable lighting
    try:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equalized = clahe.apply(gray)
        proc_img = cv2.cvtColor(equalized, cv2.COLOR_GRAY2RGB)
    except Exception:
        proc_img = image_np

    faces = detector(proc_img, 1)
    encodings = []

    for face in faces:
        shape = sp(proc_img, face)
        face_descriptor = facerec.compute_face_descriptor(proc_img, shape, 1) # 128 embedding
        encodings.append(np.array(face_descriptor))
    return encodings

@st.cache_resource
def get_trained_model():
    X = []
    y = []

    student_db = get_all_students()

    if not student_db:
        return None
    
    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))

    if len(X) == 0:
        return 0
    
    clf = SVC(kernel='linear', probability=True, class_weight='balanced')

    try:
        clf.fit(X, y)
    except ValueError:
        pass

    return {'clf': clf, 'X': X, 'y': y}


def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)

def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)
    detected_student = {}
    model_data = get_trained_model()

    if not model_data:
        return detected_student, [], len(encodings)
    
    clf = model_data['clf']
    X_train = model_data['X']
    y_train = model_data['y']

    for encoding in encodings:
        best_match_id = None
        min_distance = float('inf')
        
        # Calculate distance to all trained embeddings
        for i, train_emb in enumerate(X_train):
            dist = np.linalg.norm(train_emb - encoding)
            if dist < min_distance:
                min_distance = dist
                best_match_id = y_train[i]
        
        resemblance_threshold = 0.6  # Standard Euclidean distance threshold
        
        # Stabilize match using SVM probabilities if multi-class
        if clf and hasattr(clf, "predict_proba") and len(np.unique(y_train)) > 1:
            try:
                probs = clf.predict_proba([encoding])[0]
                best_idx = np.argmax(probs)
                if probs[best_idx] >= 0.45:
                    predicted_id = clf.classes_[best_idx]
                    # Verify using distance checks
                    dist = min([np.linalg.norm(train_emb - encoding) for idx, train_emb in enumerate(X_train) if y_train[idx] == predicted_id])
                    if dist <= resemblance_threshold:
                        best_match_id = predicted_id
                        min_distance = dist
            except Exception:
                pass

        # Only match if within resemblance threshold
        if best_match_id is not None and min_distance <= resemblance_threshold:
            detected_student[best_match_id] = True
            
    return detected_student, sorted(list(set(y_train))), len(encodings)

