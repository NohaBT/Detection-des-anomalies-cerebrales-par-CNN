import sys
import os

# ── path fix ──────────────────────────────────
# BASE_DIR = dossier dyal main.py  →  app/
# UI_DIR   = app/ui/               →  li fih toutes les pages
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR   = os.path.join(BASE_DIR, "ui")

for _p in (BASE_DIR, UI_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget,
    QWidget
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

# ── page imports ──────────────────────────────
# Les fichiers sont dans  app/ui/
from ui.login_page    import LoginPage
from ui.role_page     import RoleSelectionPage
from ui.register_page import RegisterPage
# from doctor_dashboard   import DoctorDashboardPage   ← uncomment when ready
# from patient_dashboard  import PatientDashboardPage  ← uncomment when ready
# from student_dashboard  import StudentDashboardPage  ← uncomment when ready


# ──────────────────────────────────────────────
#  MAIN WINDOW
# ──────────────────────────────────────────────
class MainWindow(QMainWindow):

    # ── page index constants ───────────────────
    PAGE_LOGIN     = 0
    PAGE_ROLE_SEL  = 1
    PAGE_REGISTER  = 2
    PAGE_DASHBOARD = 3   # reserved

    def __init__(self):
        super().__init__()

        # ── shared state ──
        self.selected_role = "Utilisateur"

        # ── window setup ──
        self.setWindowTitle("NeuroDetect")
        self.setMinimumSize(1100, 700)
        self.resize(1440, 900)

        # window icon
        ICON_PATH = os.path.join(BASE_DIR, "assets", "icons", "icon.png")
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        # dark title bar
        self.setStyleSheet("QMainWindow { background: #04080f; }")

        # ── stacked widget (page router) ──
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # ── build & register pages ──
        self._pages = {}
        self._init_pages()

        # ── start on login ──
        self.stack.setCurrentIndex(self.PAGE_LOGIN)

    # ── page initialisation ────────────────────
    def _init_pages(self):
        """Instantiate all pages and add them to the stack in order."""

        login_page = LoginPage(main_window=self)
        self.stack.insertWidget(self.PAGE_LOGIN, login_page)
        self._pages["login"] = login_page

        role_page = RoleSelectionPage(main_window=self)
        self.stack.insertWidget(self.PAGE_ROLE_SEL, role_page)
        self._pages["role"] = role_page

        # Register page built lazily (depends on selected_role)
        placeholder = QWidget()
        placeholder.setStyleSheet("background:#04080f;")
        self.stack.insertWidget(self.PAGE_REGISTER, placeholder)
        self._pages["register"] = None

        # Dashboard placeholder
        placeholder2 = QWidget()
        placeholder2.setStyleSheet("background:#04080f;")
        self.stack.insertWidget(self.PAGE_DASHBOARD, placeholder2)
        self._pages["dashboard"] = None

    # ── navigation helpers ─────────────────────
    def _switch(self, index: int):
        self.stack.setCurrentIndex(index)

    def go_login(self):
            """Reset the dashboard entirely on logout, then go to login page."""
            if self._pages.get("dashboard") is not None:
                old_dash = self.stack.widget(self.PAGE_DASHBOARD)
                self.stack.removeWidget(old_dash)
                old_dash.deleteLater()

                import PySide6.QtWidgets as QtWidgets
                placeholder = QtWidgets.QWidget()
                placeholder.setStyleSheet("background:#04080f;")
                self.stack.insertWidget(self.PAGE_DASHBOARD, placeholder)

                self._pages["dashboard"] = None

            self._switch(self.PAGE_LOGIN)

    def go_login_page(self):
        """Alias used by register / role pages for the back button."""
        self.go_login()

    def go_role_selection(self):
        self._switch(self.PAGE_ROLE_SEL)

    def go_register_page(self):
        """Rebuild RegisterPage with current role, then navigate."""
        old = self.stack.widget(self.PAGE_REGISTER)
        self.stack.removeWidget(old)
        old.deleteLater()

        new_register = RegisterPage(main_window=self)
        self.stack.insertWidget(self.PAGE_REGISTER, new_register)
        self._pages["register"] = new_register
        self._switch(self.PAGE_REGISTER)

    def go_dashboard(self):
        """Load the correct dashboard based on selected_role."""
        print("======> [DEBUG] go_dashboard() has been CALLED!")
        print(f"======> [DEBUG] Current selected role is: {self.selected_role}")
        
        if self._pages.get("dashboard") is None:
            try:
                role = self.selected_role
                if role == "Médecin":
                    from ui.doctor_dashboard import DoctorDashboardPage as Dash
                elif role == "Patient":
                    from ui.patient_dashboard import PatientDashboardPage as Dash
                elif role == "Étudiant":
                    from ui.student_dashboard import StudentDashboardPage as Dash
                else:
                    raise ImportError("No dashboard for role: " + role)

                old = self.stack.widget(self.PAGE_DASHBOARD)
                self.stack.removeWidget(old)
                old.deleteLater()
                dash = Dash(main_window=self)
                self.stack.insertWidget(self.PAGE_DASHBOARD, dash)
                self._pages["dashboard"] = dash
            except ImportError as e:
                print(f"! Error loading dashboard: {e}")
                pass   # shows placeholder until dashboard is ready
            
        print(f"======> [DEBUG] Switching to index: {self.PAGE_DASHBOARD}")  
        self._switch(self.PAGE_DASHBOARD)

    def go_back(self):
        """Generic back navigation."""
        current = self.stack.currentIndex()
        if current == self.PAGE_REGISTER:
            self._switch(self.PAGE_ROLE_SEL)
        elif current == self.PAGE_ROLE_SEL:
            self._switch(self.PAGE_LOGIN)
        elif current == self.PAGE_DASHBOARD:
            self._switch(self.PAGE_LOGIN)
        else:
            self._switch(self.PAGE_LOGIN)


# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NeuroDetect")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor("#04080f"))
    palette.setColor(QPalette.WindowText,      QColor("#f0f4ff"))
    palette.setColor(QPalette.Base,            QColor("#0d1a2e"))
    palette.setColor(QPalette.AlternateBase,   QColor("#04080f"))
    palette.setColor(QPalette.ToolTipBase,     QColor("#0d1a2e"))
    palette.setColor(QPalette.ToolTipText,     QColor("#f0f4ff"))
    palette.setColor(QPalette.Text,            QColor("#f0f4ff"))
    palette.setColor(QPalette.Button,          QColor("#0d1a2e"))
    palette.setColor(QPalette.ButtonText,      QColor("#f0f4ff"))
    palette.setColor(QPalette.BrightText,      QColor("#00d4ff"))
    palette.setColor(QPalette.Highlight,       QColor("#00d4ff"))
    palette.setColor(QPalette.HighlightedText, QColor("#04080f"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()                 