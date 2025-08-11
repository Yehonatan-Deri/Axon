# detector.py
import cv2
import numpy as np
import multiprocessing as mp
from typing import Dict, Any, Tuple, List

SENTINEL = None
MIN_AREA = 400  # lowering if still don't see detections

def _find_contours(bin_img):
    # OpenCV 3 vs 4 compatibility without needing imutils
    found = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(found) == 3:
        _, contours, _ = found
    else:
        contours, _ = found
    return contours

def _detect_motion(prev_gray: np.ndarray, gray: np.ndarray) -> Dict[str, Any]:
    """
    Detect motion between two grayscale frames.
    Returns motion flag, count of objects, and bounding boxes.
    Mirrors basic_vmd.py: absdiff -> threshold -> dilate -> contours
    """
    diff = cv2.absdiff(gray, prev_gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = _find_contours(thresh.copy())

    boxes: List[Tuple[int, int, int, int]] = []
    for c in cnts:
        if cv2.contourArea(c) < MIN_AREA:  # small noise filter; tune as needed
            continue
        x, y, w, h = cv2.boundingRect(c)
        boxes.append((x, y, w, h))

    return {
        "motion": len(boxes) > 0,
        "count": len(boxes),
        "boxes": boxes,
        # If you want to visualize downstream, you could also send 'mask': thresh
        # but it adds bandwidth. Keeping it light.
    }

def detector(in_q: mp.Queue, out_q: mp.Queue):
    """
    Receives frames from input queue, detects motion, and sends results downstream.
    Passes CONFIG messages unchanged.
    """
    prev_gray = None

    try:
        while True:
            item = in_q.get()
            if item is SENTINEL:
                # propagate the sentinel and exit
                out_q.put(SENTINEL)
                break

            # pass configuration through unchanged
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "CONFIG":
                out_q.put(item)
                continue

            frame = item  # NOT modify this frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is None:
                detections = {"motion": False, "count": 0, "boxes": []}
            else:
                detections = _detect_motion(prev_gray, gray)

            # Update prev_gray *after* detection
            prev_gray = gray

            # Send original frame + detection metadata
            out_q.put((frame, detections))

    except KeyboardInterrupt:
        pass
    finally:
        # Make sure downstream is released even on error
        out_q.put(SENTINEL)
