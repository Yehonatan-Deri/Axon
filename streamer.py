# streamer.py
import cv2
import multiprocessing as mp

SENTINEL = None

def streamer(video_path: str, out_q: mp.Queue):
    cap = cv2.VideoCapture(video_path)
    try:
        if not cap.isOpened():
            print(f"[Streamer] Failed to open: {video_path}")
            out_q.put(SENTINEL)
            return

        # >>> NEW: read FPS and send a config packet downstream
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        if fps <= 0:
            fps = 30.0  # sensible fallback
        out_q.put(("CONFIG", {"fps": float(fps)}))
        # <<<

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

if __name__ == "__main__":
    # Minimal example of just running the streamer alone
    q_frames = mp.Queue(maxsize=64)
    p = mp.Process(target=streamer, args=("PATH_TO_VID.mp4", q_frames), daemon=True)
    p.start()
    p.join()
