# display.py
import cv2
import multiprocessing as mp
from datetime import datetime

SENTINEL = None

def display(in_q: mp.Queue, window_name: str = "Video"):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    #
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

    try:
        while True:
            item = in_q.get()
            if item is SENTINEL:
                break

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
            cv2.putText(frame, f"motion: {detections['motion']} count: {detections['count']}",
                        (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.LINE_AA)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(30) & 0xFF
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
