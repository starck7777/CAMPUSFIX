import shutil
import socket
import subprocess
import sys
import time
import webbrowser
import ctypes
from pathlib import Path
from urllib.request import urlopen


BASE_DIR = Path(__file__).resolve().parent
APP_URL = "http://127.0.0.1:5000/"
HOST = "127.0.0.1"
PORT = 5000


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def wait_for_server(timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open(HOST, PORT):
            try:
                with urlopen(APP_URL, timeout=1):
                    return True
            except Exception:
                time.sleep(0.25)
                continue
        time.sleep(0.25)
    return False


def start_server():
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    python = str(pythonw if pythonw.exists() else Path(sys.executable))
    return subprocess.Popen(
        [python, str(BASE_DIR / "run_campusfix.pyw")],
        cwd=BASE_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def launch_app_window():
    browser_candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]

    for browser in browser_candidates:
        if browser.exists():
            return subprocess.Popen([str(browser), f"--app={APP_URL}"], cwd=BASE_DIR)

    firefox = shutil.which("firefox")
    if firefox:
        return subprocess.Popen([firefox, "--new-window", APP_URL], cwd=BASE_DIR)

    webbrowser.open(APP_URL)
    return None


def main() -> None:
    server_process = None
    if not is_port_open(HOST, PORT):
        server_process = start_server()

    if not wait_for_server():
        raise SystemExit("CampusFix could not be started.")

    browser_process = launch_app_window()
    if server_process and browser_process:
        browser_process.wait()
        server_process.terminate()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        ctypes.windll.user32.MessageBoxW(
            None,
            f"CampusFix could not start.\n\n{exc}",
            "CampusFix",
            0x10,
        )
