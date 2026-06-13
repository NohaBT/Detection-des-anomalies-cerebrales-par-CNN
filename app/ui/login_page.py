import os
import sys
import math
import random

# ── path fix: zid app/ l sys.path bach yalqa database.py ──
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit,
    QFrame, QVBoxLayout, QHBoxLayout,
    QCheckBox, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QBrush
from PySide6.QtCore import Qt, QTimer

from database import login_user

# ──────────────────────────────────────────────
#  NEURAL CANVAS
# ──────────────────────────────────────────────
class NeuralCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._nodes = []
        self._init_nodes()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)

    def _init_nodes(self, n=65):
        w = max(self.width(), 1600)
        h = max(self.height(), 900)
        self._nodes = [
            {
                "x":  random.uniform(0, w),
                "y":  random.uniform(0, h),
                "vx": random.uniform(-0.35, 0.35),
                "vy": random.uniform(-0.35, 0.35),
                "r":  random.uniform(1.2, 2.8),
                "ph": random.uniform(0, math.pi * 2),
            }
            for _ in range(n)
        ]

    def _step(self):
        w, h = self.width(), self.height()
        for nd in self._nodes:
            nd["x"] += nd["vx"]; nd["y"] += nd["vy"]
            nd["ph"] += 0.018
            if nd["x"] < 0 or nd["x"] > w: nd["vx"] *= -1
            if nd["y"] < 0 or nd["y"] > h: nd["vy"] *= -1
        self.update()

    def resizeEvent(self, e):
        self._init_nodes()
        super().resizeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for i, a in enumerate(self._nodes):
            for b in self._nodes[i+1:]:
                dx, dy = a["x"] - b["x"], a["y"] - b["y"]
                dist = math.hypot(dx, dy)
                if dist < 150:
                    alpha = int((1 - dist / 150) * 65)
                    pen = QPen(QColor(0, 180, 255, alpha))
                    pen.setWidthF(0.7)
                    p.setPen(pen)
                    p.drawLine(int(a["x"]), int(a["y"]), int(b["x"]), int(b["y"]))
        p.setPen(Qt.NoPen)
        for nd in self._nodes:
            glow  = 0.6 + 0.4 * math.sin(nd["ph"])
            alpha = int(180 * glow)
            r     = nd["r"] * glow
            p.setBrush(QBrush(QColor(0, 212, 255, alpha)))
            p.drawEllipse(int(nd["x"] - r), int(nd["y"] - r), int(r * 2), int(r * 2))
        p.end()


# ──────────────────────────────────────────────
#  SHARED STYLES
# ──────────────────────────────────────────────
FIELD_STYLE = """
QLineEdit {
    background: rgba(255,255,255,0.06);
    color: #f0f4ff;
    border-radius: 11px;
    border: 1px solid rgba(255,255,255,0.10);
    padding-left: 14px;
    font-size: 13px;
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
}
QLineEdit:focus {
    border: 1px solid rgba(0,212,255,0.55);
    background: rgba(255,255,255,0.09);
}
QLineEdit:hover:!focus {
    border: 1px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.08);
}
"""


def _lbl(text, size=12, color="rgba(240,244,255,0.45)",
         bold=False, family="'DM Sans','Segoe UI',sans-serif") -> QLabel:
    w = QLabel(text)
    w.setStyleSheet(
        f"color:{color}; font-size:{size}px; font-weight:{'700' if bold else '400'};"
        f"font-family:{family}; background:transparent; border:none;"
    )
    return w


# ──────────────────────────────────────────────
#  ERROR BANNER
# ──────────────────────────────────────────────
class ErrorBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        vb = QVBoxLayout(self)
        vb.setContentsMargins(14, 8, 14, 8)
        vb.addWidget(self._lbl)
        self.hide()

    def show_error(self, msg: str):
        self.setStyleSheet("QFrame{background:rgba(255,77,109,0.10);border:1px solid rgba(255,77,109,0.30);border-radius:10px;}")
        self._lbl.setStyleSheet("color:#ff4d6d;font-size:12px;background:transparent;border:none;font-family:'DM Sans','Segoe UI',sans-serif;")
        self._lbl.setText(f"⚠  {msg}")
        self.show()

    def show_success(self, msg: str):
        self.setStyleSheet("QFrame{background:rgba(52,211,153,0.10);border:1px solid rgba(52,211,153,0.30);border-radius:10px;}")
        self._lbl.setStyleSheet("color:#34d399;font-size:12px;background:transparent;border:none;font-family:'DM Sans','Segoe UI',sans-serif;")
        self._lbl.setText(f"✅  {msg}")
        self.show()

    def clear(self):
        self.hide()
        self._lbl.setText("")


# ──────────────────────────────────────────────
#  LOGIN PAGE
# ──────────────────────────────────────────────
class LoginPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background: #04080f;")

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        IMG_PATH = os.path.join(BASE_DIR, "assets", "medical.jpg")

        self.bg = QLabel(self)
        if os.path.exists(IMG_PATH):
            self.bg.setPixmap(QPixmap(IMG_PATH))
            self.bg.setScaledContents(True)
        else:
            self.bg.setStyleSheet("background:#04080f;")

        self.img_overlay = QFrame(self)
        self.img_overlay.setStyleSheet("background:rgba(4,8,15,0.72); border:none;")
        self.canvas = NeuralCanvas(self)
        self.vignette = QLabel(self)
        self.vignette.setStyleSheet("""
            background: qradialgradient(cx:0.5,cy:0.5,radius:0.8,
                stop:0 rgba(0,0,0,0), stop:1 rgba(0,0,0,0.60));
        """)

        self.ui = QWidget(self)
        self.ui.setStyleSheet("background:transparent;")
        root = QHBoxLayout(self.ui)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_left(), stretch=3)
        root.addWidget(self._build_right(), stretch=2)

        self.bg.lower(); self.img_overlay.raise_()
        self.canvas.raise_(); self.vignette.raise_(); self.ui.raise_()

    # ── LEFT ───────────────────────────────────
    def _build_left(self) -> QWidget:
        panel = QWidget(); panel.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(panel)
        vb.setContentsMargins(80, 60, 40, 60)
        vb.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        vb.setSpacing(0)

        brand_row = QHBoxLayout(); brand_row.setSpacing(12)
        icon_box = QLabel("🧠"); icon_box.setFixedSize(46, 46)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet("font-size:22px;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00d4ff,stop:1 #0066ff);border-radius:12px;")
        brand_lbl = _lbl("NeuroDetect", size=18, color="#f0f4ff", bold=True,
                          family="'Syne','Segoe UI Black',sans-serif")
        brand_row.addWidget(icon_box); brand_row.addWidget(brand_lbl); brand_row.addStretch()
        vb.addLayout(brand_row); vb.addSpacing(40)

        hero = QLabel("Bienvenue\nsur NeuroDetect.")
        hero.setStyleSheet("color:#f0f4ff;font-size:46px;font-weight:800;font-family:'Syne','Segoe UI Black',sans-serif;line-height:1.05;background:transparent;letter-spacing:-0.02em;")
        vb.addWidget(hero); vb.addSpacing(18)

        accent_line = QFrame(); accent_line.setFixedSize(56, 3)
        accent_line.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00d4ff,stop:1 #0066ff);border-radius:2px;border:none;")
        vb.addWidget(accent_line); vb.addSpacing(20)

        sub = _lbl("Plateforme intelligente de détection\ndes tumeurs cérébrales par IA.",
                   size=13, color="rgba(240,244,255,0.50)")
        sub.setStyleSheet(sub.styleSheet() + " line-height:1.7; font-weight:300;")
        vb.addWidget(sub); vb.addSpacing(40)

        stats = [("90%", "Précision IA"), ("2s", "Temps d'analyse")]
        stats_row = QHBoxLayout(); stats_row.setSpacing(0)
        for i, (val, label) in enumerate(stats):
            col = QVBoxLayout(); col.setSpacing(2)
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet("color:#00d4ff;font-size:26px;font-weight:800;font-family:'Syne','Segoe UI Black',sans-serif;background:transparent;")
            col.addWidget(val_lbl)
            col.addWidget(_lbl(label, size=11, color="rgba(240,244,255,0.40)"))
            stats_row.addLayout(col)
            if i < len(stats) - 1:
                sep = QFrame(); sep.setFixedSize(1, 40)
                sep.setStyleSheet("background:rgba(255,255,255,0.10);border:none;")
                stats_row.addSpacing(24); stats_row.addWidget(sep, alignment=Qt.AlignVCenter); stats_row.addSpacing(24)
        stats_row.addStretch()
        vb.addLayout(stats_row); vb.addStretch()

        badge_row = QHBoxLayout(); badge_row.setSpacing(8)
        for badge in ["CE Médical", "ISO 27001", "HL7 FHIR"]:
            b = QLabel(badge)
            b.setStyleSheet("color:rgba(240,244,255,0.35);font-size:10px;font-family:'DM Sans','Segoe UI',sans-serif;letter-spacing:0.08em;border:1px solid rgba(255,255,255,0.08);border-radius:100px;padding:4px 14px;background:rgba(255,255,255,0.03);")
            badge_row.addWidget(b)
        badge_row.addStretch()
        vb.addLayout(badge_row)
        return panel

    # ── RIGHT CARD ─────────────────────────────
    def _build_right(self) -> QWidget:
        wrapper = QWidget(); wrapper.setStyleSheet("background:transparent;")
        wvb = QVBoxLayout(wrapper)
        wvb.setContentsMargins(0, 0, 70, 0)
        wvb.setAlignment(Qt.AlignVCenter)

        card = QFrame(); card.setFixedWidth(420)
        card.setStyleSheet("QFrame{background:rgba(8,16,32,0.90);border-radius:24px;border:none;}")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(80); shadow.setOffset(0, 24)
        shadow.setColor(QColor(0, 0, 0, 160)); card.setGraphicsEffect(shadow)

        vb = QVBoxLayout(card)
        vb.setContentsMargins(32, 34, 32, 34); vb.setSpacing(0)

        tag = QLabel("Connexion sécurisée")
        tag.setAlignment(Qt.AlignCenter); tag.setFixedHeight(28)
        tag.setStyleSheet("color:#00d4ff;font-size:11px;font-family:'DM Sans','Segoe UI',sans-serif;letter-spacing:0.10em;background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.22);border-radius:100px;padding:4px 18px;")
        vb.addWidget(tag, alignment=Qt.AlignCenter); vb.addSpacing(18)

        title = QLabel("Se connecter"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#f0f4ff;font-size:26px;font-weight:700;font-family:'Syne','Segoe UI Black',sans-serif;background:transparent;letter-spacing:-0.01em;")
        sub_title = _lbl("Accédez à votre espace personnel", size=12, color="rgba(240,244,255,0.38)")
        sub_title.setAlignment(Qt.AlignCenter)
        sub_title.setStyleSheet(sub_title.styleSheet() + " font-weight:300;")
        vb.addWidget(title); vb.addSpacing(4); vb.addWidget(sub_title); vb.addSpacing(22)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet("background:rgba(255,255,255,0.07);border:none;")
        vb.addWidget(div); vb.addSpacing(16)

        # banner
        self._banner = ErrorBanner()
        vb.addWidget(self._banner); vb.addSpacing(4)

        # fields
        def field_group(label_text, widget):
            col = QVBoxLayout(); col.setSpacing(5)
            col.addWidget(_lbl(label_text.upper(), size=10, color="rgba(240,244,255,0.38)"))
            col.addWidget(widget); return col

        self.identifier = QLineEdit()
        self.identifier.setPlaceholderText("Nom d'utilisateur ou e-mail")
        self.identifier.setFixedHeight(46); self.identifier.setStyleSheet(FIELD_STYLE)
        self.identifier.textChanged.connect(self._banner.clear)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Mot de passe")
        self.password.setFixedHeight(46)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet(FIELD_STYLE)
        self.password.textChanged.connect(self._banner.clear)
        self.password.returnPressed.connect(self._handle_login)

        vb.addLayout(field_group("Identifiant", self.identifier)); vb.addSpacing(12)
        vb.addLayout(field_group("Mot de passe", self.password)); vb.addSpacing(14)

        row = QHBoxLayout()
        remember = QCheckBox("Se souvenir de moi")
        remember.setStyleSheet("QCheckBox{color:rgba(240,244,255,0.50);font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;spacing:7px;}QCheckBox::indicator{width:15px;height:15px;border-radius:4px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.05);}QCheckBox::indicator:checked{background:#00d4ff;border:1px solid #00d4ff;}")
        forgot = QPushButton("Mot de passe oublié ?")
        forgot.setFlat(True); forgot.setCursor(Qt.PointingHandCursor)
        forgot.setStyleSheet("QPushButton{background:transparent;color:#00d4ff;border:none;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;}QPushButton:hover{color:#f0f4ff;}")
        row.addWidget(remember); row.addStretch(); row.addWidget(forgot)
        vb.addLayout(row); vb.addSpacing(22)

        self._login_btn = QPushButton("SE CONNECTER")
        self._login_btn.setFixedHeight(50); self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.setStyleSheet("""
            QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00d4ff,stop:1 #0066ff);
                color:white;border:none;border-radius:12px;font-size:13px;font-weight:700;
                font-family:'Syne','Segoe UI Black',sans-serif;letter-spacing:0.12em;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33ddff,stop:1 #2288ff);}
            QPushButton:pressed{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00aacc,stop:1 #0044cc);}
            QPushButton:disabled{background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.30);}
        """)
        self._login_btn.clicked.connect(self._handle_login)
        vb.addWidget(self._login_btn); vb.addSpacing(10)

        or_row = QHBoxLayout()
        for i in range(2):
            line = QFrame(); line.setFixedHeight(1)
            line.setStyleSheet("background:rgba(255,255,255,0.07);border:none;")
            or_row.addWidget(line)
            if i == 0:
                or_lbl = _lbl("ou", size=11, color="rgba(240,244,255,0.25)")
                or_lbl.setAlignment(Qt.AlignCenter)
                or_row.addWidget(or_lbl); or_row.setSpacing(12)
        vb.addSpacing(6); vb.addLayout(or_row); vb.addSpacing(10)

        reg_btn = QPushButton("Créer un nouveau compte")
        reg_btn.setFixedHeight(44); reg_btn.setCursor(Qt.PointingHandCursor)
        reg_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.04);color:rgba(240,244,255,0.65);border:1px solid rgba(255,255,255,0.09);border-radius:12px;font-size:13px;font-family:'DM Sans','Segoe UI',sans-serif;}QPushButton:hover{background:rgba(255,255,255,0.08);color:#f0f4ff;border:1px solid rgba(255,255,255,0.16);}")
        if self.main_window:
            reg_btn.clicked.connect(self.main_window.go_role_selection)
        vb.addWidget(reg_btn); vb.addSpacing(20)

        div2 = QFrame(); div2.setFixedHeight(1)
        div2.setStyleSheet("background:rgba(255,255,255,0.06);border:none;")
        vb.addWidget(div2); vb.addSpacing(16)

        footer = _lbl("Plateforme sécurisée · Données médicales chiffrées",
                       size=10, color="rgba(240,244,255,0.18)")
        footer.setAlignment(Qt.AlignCenter)
        vb.addWidget(footer)

        wvb.addWidget(card)
        return wrapper

    # ── LOGIN HANDLER ──────────────────────────
    def _handle_login(self):
        identifier = self.identifier.text().strip()
        pwd        = self.password.text()

        if not identifier or not pwd:
            self._banner.show_error("Veuillez remplir tous les champs.")
            return

        self._login_btn.setEnabled(False)
        self._login_btn.setText("Connexion...")

        success, msg, user_data = login_user(identifier, pwd)

        self._login_btn.setEnabled(True)
        self._login_btn.setText("SE CONNECTER")

        if not success:
            self._banner.show_error(msg)
            self.password.clear()
            return

        self._banner.clear()
        self.identifier.clear()
        self.password.clear()

        if self.main_window:
            self.main_window.current_user  = user_data
            self.main_window.selected_role = user_data["role"]
            self.main_window.go_dashboard()

    # ── resize ────────────────────────────────
    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        for widget in (self.bg, self.img_overlay, self.canvas, self.vignette, self.ui):
            widget.setGeometry(0, 0, w, h)
        super().resizeEvent(event)