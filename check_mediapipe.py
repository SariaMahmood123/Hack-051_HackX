try:
    import mediapipe as mp
    print(f"mediapipe {mp.__version__}")
except ImportError:
    print("mediapipe not available")
