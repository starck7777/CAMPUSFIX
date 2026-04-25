import ctypes
import socket
import threading
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from werkzeug.serving import make_server

from app import RESOURCE_DIR, app, init_db


class ServerThread(threading.Thread):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(daemon=True)
        self._server = make_server(host, port, app)

    def run(self) -> None:
        self._server.serve_forever()

    def shutdown(self) -> None:
        self._server.shutdown()


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main() -> None:
    init_db()
    port = get_free_port()
    server = ServerThread("127.0.0.1", port)
    server.start()

    qt_app = QApplication([])
    icon_path = Path(RESOURCE_DIR) / "static" / "campusfix-shortcut.ico"
    if icon_path.exists():
        qt_app.setWindowIcon(QIcon(str(icon_path)))

    window = QWebEngineView()
    window.setWindowTitle("CampusFix")
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.resize(1280, 820)
    window.setMinimumSize(960, 640)
    window.load(QUrl(f"http://127.0.0.1:{port}/"))

    try:
        window.show()
        qt_app.exec()
    finally:
        server.shutdown()


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
