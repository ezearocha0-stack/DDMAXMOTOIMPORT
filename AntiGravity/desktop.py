import webview
import threading
from run import app

def start_flask():
    app.run()

if __name__ == '__main__':
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    webview.create_window("Sistema de Motocicletas", "http://127.0.0.1:5000")
    webview.start()