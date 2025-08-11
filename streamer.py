# streamer.py
import cv2
import multiprocessing as mp

SENTINEL = None

def streamer(video_path: str, out_q: mp.Queue):
    """
    Reads frames from a video file and sends them to the output queue.
    Sends a CONFIG packet with FPS before sending frames.
    """
    cap = cv2.VideoCapture(video_path)
    try:
        if not cap.isOpened():
            print(f"[Streamer] Failed to open: {video_path}")
            out_q.put(SENTINEL)
            return

        # read FPS and send a config packet downstream
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        if fps <= 0:
            fps = 30.0  # sensible fallback
        out_q.put(("CONFIG", {"fps": float(fps)}))

        # Read and send frames until the video ends
        while True:
            ret, frame = cap.read()
            if not ret:
                # End of video
                break
            # Send raw frame downstream
            out_q.put(frame)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        # Signal downstream that we are done
        out_q.put(SENTINEL)