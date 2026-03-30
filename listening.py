import socket
from pathlib import Path
from datetime import datetime
import threading

import cv2
import numpy as np
import socket

from dcam import *

# =========================
# Settings
# =========================
HOST = "0.0.0.0"      # listen on all network interfaces
PORT = 5000           # choose a port
SAVE_DIR = Path(r"C:\camera_data")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

capture_lock = threading.Lock()


# =========================
# Utilities
# =========================
def sanitize_filename(name: str) -> str:
    """
    Keep filename safe for Windows.
    """
    invalid = '<>:"/\\|?*'
    name = name.strip()
    for ch in invalid:
        name = name.replace(ch, "_")
    name = name.replace(" ", "_")
    return name


def save_frame_as_tiff(data: np.ndarray, filepath: Path):
    if data is None:
        raise RuntimeError("No image data returned from camera")

    if data.dtype != np.uint16:
        raise RuntimeError(f"Expected uint16 image, got {data.dtype}")

    ok = cv2.imwrite(str(filepath), data)
    if not ok:
        raise RuntimeError(f"Failed to save image to {filepath}")


def capture_one_frame(dcam: Dcam, timeout_millisec=2000) -> np.ndarray:
    """
    Start capture, wait for one frame, return that frame.
    """
    if not dcam.cap_start():
        raise RuntimeError(f"Dcam.cap_start() failed: {dcam.lasterr()}")

    try:
        if not dcam.wait_capevent_frameready(timeout_millisec):
            dcamerr = dcam.lasterr()
            if dcamerr.is_timeout():
                raise TimeoutError("Timed out waiting for frame ready")
            raise RuntimeError(f"wait_capevent_frameready failed: {dcamerr}")

        data = dcam.buf_getlastframedata()
        if data is None:
            raise RuntimeError("buf_getlastframedata() returned None")

        return data.copy()

    finally:
        dcam.cap_stop()

def get_local_ip():
    """
    Get the IP address used for outgoing connections (most reliable way).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't actually send anything
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def handle_command(dcam: Dcam, cmd: str) -> str:
    """
    Receive one filename string, capture one image, save it.

    Example received text:
        test001
        sample_A
        my_trace_42
    """
    raw_name = cmd.strip()
    if not raw_name:
        return "ERR empty_filename"

    safe_name = sanitize_filename(raw_name)
    if not safe_name:
        return "ERR invalid_filename"

    filepath = SAVE_DIR / f"{safe_name}.tif"

    # Avoid two captures at once
    with capture_lock:
        frame = capture_one_frame(dcam, timeout_millisec=2000)
        save_frame_as_tiff(frame, filepath)

    return f"OK saved={filepath}"


# =========================
# Main server
# =========================
def run_camera_server(iDevice=0):
    if not Dcamapi.init():
        print(f"-NG: Dcamapi.init() fails with error {Dcamapi.lasterr()}")
        return

    dcam = Dcam(iDevice)

    try:
        if not dcam.dev_open():
            print(f"-NG: Dcam.dev_open() fails with error {dcam.lasterr()}")
            return

        if not dcam.buf_alloc(3):
            print(f"-NG: Dcam.buf_alloc(3) fails with error {dcam.lasterr()}")
            return

        print(f"Camera ready. Saving to: {SAVE_DIR}")
        local_ip = get_local_ip()
        print("====================================")
        print(f"Camera server is running")
        print(f"Send commands to: {local_ip}:{PORT}")
        print(f"Saving images to: {SAVE_DIR}")
        print("====================================")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((HOST, PORT))
            server.listen(5)

            while True:
                conn, addr = server.accept()
                with conn:
                    try:
                        data = conn.recv(4096).decode("utf-8").strip()
                        print(f"Received from {addr}: {data}")

                        reply = handle_command(dcam, data)

                    except Exception as e:
                        reply = f"ERR {e}"

                    conn.sendall((reply + "\n").encode("utf-8"))
                    print(f"Reply: {reply}")

    finally:
        try:
            dcam.buf_release()
        except Exception:
            pass

        try:
            dcam.dev_close()
        except Exception:
            pass

        Dcamapi.uninit()


if __name__ == "__main__":
    run_camera_server()