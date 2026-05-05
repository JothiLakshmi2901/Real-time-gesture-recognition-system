Real-Time Gesture Recognition System

A real-time gesture recognition web application that detects hand gestures using a webcam and converts them into meaningful outputs. This system is designed to assist differently-abled users in communication, especially in real-world scenarios like restaurants.

📚 Table of Contents
Overview
Features
Technologies Used
How It Works
System Workflow
Model Details
Project Structure
Run Instructions
Output
Future Scope


📌 Overview

This project uses MediaPipe and Deep Learning to recognize hand gestures in real-time.
It captures hand landmarks from live video, processes them into feature vectors, and predicts gestures using a trained neural network model.

The system is integrated with a Flask-based web application, enabling user interaction through a browser interface.

🚀 Features
    ✋ Real-time hand gesture detection
    🎯 Accurate gesture prediction using ANN model
    📷 Webcam-based live input
    21 hand landmarks extraction (63 features)
    ⚡ Fast and efficient prediction pipeline
    🌐 Web-based interface using Flask
    🧠 Confidence-based filtering for reliable output


🛠️ Technologies Used

┌----------------------------------------------------------------┐
|    Technology	            |             Purpose                |
|----------------------------------------------------------------|
|    Python	            | Core programming language              |
|    OpenCV	            | Video capture and frame processing     |
|    MediaPipe	        | Hand landmark detection                |
|    TensorFlow	        | Model training and prediction          |
|    NumPy	            | Numerical computations                 |
|    Flask	            | Web application backend                |
|    Pickle	            | Label encoding storage                 |
└----------------------------------------------------------------┘


⚙️ How It Works

The system processes live video input and performs gesture recognition through the following steps:

Webcam Input → Hand Detection → Landmark Extraction → Feature Vector → Model Prediction → Output Display


🔄 System Workflow


┌────────────────────────────┐
│      Webcam Input          │
└────────────┬───────────────┘
             │
     ┌───────▼────────┐
     │ MediaPipe Hands│
     └───────┬────────┘
             │
     ┌───────▼──────────────┐
     │ Extract Landmarks    │
     │ (21 points → 63 data)│
     └───────┬──────────────┘
             │
     ┌───────▼───────────┐
     │ Feature Vector    │
     └───────┬───────────┘
             │
     ┌───────▼───────────┐
     │ ANN Model Predict │
     └───────┬───────────┘
             │
     ┌───────▼───────────┐
     │ Display Output    │
     └───────────────────┘


📊 Model Details:

Input: 63 features (21 landmarks × x, y, z)
Model Type: Artificial Neural Network (ANN)
Activation:
Hidden Layers → ReLU
Output Layer → Softmax
Optimizer: Adam
Loss Function: Sparse Categorical Crossentropy


📂 Project Structure


GestureRecognition/
│
├── data/
│   └── static_data/
│       └── static_data.csv
│
├── models/
│   ├── static_model.h5
│   └── static_labels.pkl
│
├── src/
│   └── source/
│       ├── collect_static.py
│       ├── train_static.py
│       └── predict_static.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── index.html
│   └── detect.html
│
├── app.py
├── README.md
└── requirements.txt


▶️ Run Instructions

Prerequisites
Python 3.10+
Webcam
Steps
# Clone repository
git clone https://github.com/your-username/gesture-recognition.git

# Navigate to project
cd gesture-recognition

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py


🎯 Use Cases

Assistive communication system
Restaurant interaction system
Gesture-based control systems
Accessibility-focused applications


🔮 Future Scope

Add dynamic gesture recognition
Integrate Text-to-Speech (TTS)
Improve accuracy with larger dataset
Deploy as cloud-based application
Mobile application integration


👩‍💻 Author

Jothi Lakshmi


📄 License

This project is licensed under the MIT License.
