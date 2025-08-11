# main.py
import multiprocessing as mp
from streamer import streamer
from detector import detector
from display import display

if __name__ == "__main__":
    mp.set_start_method("spawn")  # safer cross‑platform

    q_frames = mp.Queue(maxsize=64)
    q_results = mp.Queue(maxsize=64)

    video_path = "People - 6387.mp4"

    p_stream = mp.Process(target=streamer, args=(video_path, q_frames), daemon=True)
    p_detect = mp.Process(target=detector, args=(q_frames, q_results), daemon=True)
    p_show   = mp.Process(target=display,  args=(q_results,), daemon=True)

    try:
        p_stream.start()
        p_detect.start()
        p_show.start()

        # Wait for display to finish (it will close on sentinel or ESC)
        p_show.join()

    except KeyboardInterrupt:
        pass
    finally:
        # Best-effort cleanup: terminate any stragglers
        for p in (p_stream, p_detect, p_show):
            if p.is_alive():
                p.terminate()
        for p in (p_stream, p_detect, p_show):
            p.join()
