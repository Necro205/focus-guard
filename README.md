# 🎯 FocusGuard — Smart Productivity Assistant

An AI-powered application that uses a webcam, object detection, and system monitoring to identify distractions during study sessions in real-time and generates detailed statistical reports upon completion.

## 📚 Academic Context

| Field | Applied Topics |
| :--- | :--- |
| **Computer Vision** | Facial landmark detection, head pose estimation (solvePnP), Eye Aspect Ratio (EAR), and YOLOv8-based object detection |
| **Statistics** | Descriptive statistics, time series analysis of focus levels, correlation matrices, and hypothesis testing |
| **Software Engineering** | Modular software architecture, multi-thread management, GUI design, and automated report generation |

## 🚀 Installation

Ensure you have Python installed, then follow these steps to set up your environment:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # For Linux/Mac
venv\Scripts\activate         # For Windows

# Install dependencies and run the application
pip install -r requirements.txt
python main.py
```

## 🗂 Project Structure

The project follows a modular hierarchy to ensure maintainability and organized data management:

* **`main.py`**: The primary entry point for the GUI and application orchestration.
* **`config.py`**: Configuration constants and global settings.
* **`modules/`**: Contains core logic for AI components like face and phone detection.
* **`data_structures/`**: Custom implementations for handling session data efficiently.
* **`reports/`**: Stores generated session summaries and technical presentations.
* **`yolov8n.pt`**: Pre-trained YOLOv8 model file for real-time object detection.

## 🎮 Usage

1.  **Launch**: Run `python main.py` to open the FocusGuard interface.
2.  **Start Session**: Click the "Start Session" button to activate the webcam and begin monitoring.
3.  **Active Tracking**: The system calculates your focus score in real-time based on posture and active screen windows.
4.  **Instant Alerts**: Receive immediate visual or auditory feedback when a distraction is detected.
5.  **Analytics**: Click "End Session" to automatically generate and view a detailed HTML productivity report.
