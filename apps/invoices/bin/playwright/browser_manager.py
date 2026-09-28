# pylint: disable=E0401,C0413
"""
FR : Singleton de gestion du navigateur Playwright pour la génération de PDF
EN : Playwright browser singleton manager for PDF generation

Commentaire:
    Le browser Chromium est lancé une seule fois et réutilisé pour toutes
    les générations de PDF, ce qui évite le coût de lancement (~300-500ms)
    à chaque appel.

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""
import atexit
import threading

from playwright.sync_api import sync_playwright


class BrowserManager:
    """
    Singleton thread-safe qui maintient une instance Chromium en vie
    pour réutilisation entre les générations de PDF.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _initialize(self):
        if not self._initialized:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._initialized = True
            atexit.register(self.close)

    @property
    def browser(self):
        self._initialize()
        return self._browser

    def new_page(self):
        return self.browser.new_page()

    def close(self):
        if self._initialized:
            try:
                self._browser.close()
                self._playwright.stop()
            except Exception:
                pass
            self._initialized = False


# Instance globale réutilisable
_manager = BrowserManager()


def get_browser_manager() -> BrowserManager:
    return _manager