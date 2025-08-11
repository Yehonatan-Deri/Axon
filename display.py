# display.py
import cv2
import multiprocessing as mp
from datetime import datetime
from typing import Dict, Any, List, Tuple

SENTINEL = None

def blur_regions_bgr(frame, boxes: List[Tuple[int,int,int,int]], ksize=(21,21), sigmaX=0):
    """
    Apply Gaussian blur only to rectangular regions given by boxes (x,y,w,h).
    Operates in-place on 'frame' and returns it.
    """
    h, w = frame.shape[:2]
    for (x, y, bw, bh) in boxes:
        x0 = max(0, x); y0 = max(0, y)
        x1 = min(w, x + bw); y1 = min(h, y + bh)
        if x1 > x0 and y1 > y0:
            roi = frame[y0:y1, x0:x1]
            blurred = cv2.GaussianBlur(roi, ksize, sigmaX)
            frame[y0:y1, x0:x1] = blurred
    return frame

def display(in_q: mp.Queue, window_name: str = "Video"):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # >>> NEW: make window full-screen
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
    # <<<

    try:
        while True:
            item = in_q.get()
            if item is SENTINEL:
                break

            # >>> NEW: handle CONFIG to get FPS
            if (
                    isinstance(item, tuple)
                    and len(item) == 2
                    and isinstance(item[0], str)
                    and item[0] == "CONFIG"):
                cfg = item[1] or {}
                fps = float(cfg.get("fps", 30.0)) or 30.0
                fps = int(fps)
                continue
            # <<<

            frame, detections = item  # detections dict (motion, count, boxes)

            # Timestamp (top-left corner)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame,
                ts,
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # (Optional) If you want to visualize metadata, uncomment:
            for (x, y, w, h) in detections.get("boxes", []):
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame,
                        f"motion: {detections['motion']} count: {detections['count']}",
                        (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0,255,0),
                        2,
                        cv2.LINE_AA)

            # NEW: blur only detected regions
            # boxes = detections.get("boxes", [])
            # if boxes:
            #     blur_regions_bgr(frame, boxes)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(fps) & 0xFF
            if key == 27:  # ESC to close early
                break

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Minimal example: just reads from a queue and shows; feed it in a real run.
    q_results = mp.Queue(maxsize=64)
    p = mp.Process(target=display, args=(q_results,), daemon=True)
    p.start()
    # Remember to feed q_results and then send None in a real run.
    p.join()
