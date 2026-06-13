import os
import math
import random

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QFrame, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect
)
from PySide6.QtGui import (
    QPixmap, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QCursor
)
from PySide6.QtCore import Qt, QTimer, QRect, QPoint


# ──────────────────────────────────────────────
#  NEURAL CANVAS  (Arrière-plan dynamique)
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
#  ROLE CARD (Bouton de profil)
# ──────────────────────────────────────────────
class RoleCard(QFrame):
    """Carte de rôle cliquable et centrée verticalement."""

    def __init__(self, icon: str, title: str, desc: str, role_key: str,
                 on_click=None, parent=None):
        super().__init__(parent)
        self.role_key = role_key
        self._on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(94) 
        self._hovered = False

        self.setObjectName("RoleCard")
        self.setStyleSheet(self._style(False))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(18)

        # Icône arrondie
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(46, 46)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("""
            font-size: 22px;
            background: rgba(0,212,255,0.10);
            border: 1px solid rgba(0,212,255,0.20);
            border-radius: 23px;
        """)

        # Bloc de textes parfaitement centré au milieu
        text_block = QVBoxLayout()
        text_block.setSpacing(1)
        text_block.setContentsMargins(0, 0, 0, 0)
        text_block.setAlignment(Qt.AlignVCenter) 

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            color: #f0f4ff;
            font-size: 15px;
            font-weight: 700;
            font-family: 'Syne','Segoe UI Black',sans-serif;
            background: transparent;
            letter-spacing: 0.02em;
            padding: 0px;
            margin: 0px;
        """)
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("""
            color: rgba(240,244,255,0.45);
            font-size: 11px;
            font-family: 'DM Sans','Segoe UI',sans-serif;
            background: transparent;
            font-weight: 300;
            padding: 0px;
            margin: 0px;
        """)
        text_block.addWidget(title_lbl)
        text_block.addWidget(desc_lbl)

        # Flèche d'action droite
        arrow = QLabel("→")
        arrow.setStyleSheet("""
            color: rgba(0,212,255,0.55);
            font-size: 18px;
            background: transparent;
        """)

        layout.addWidget(icon_lbl, alignment=Qt.AlignVCenter)
        layout.addLayout(text_block)
        layout.addStretch()
        layout.addWidget(arrow, alignment=Qt.AlignVCenter)

        # Ombre portée de la carte
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    def _style(self, hovered: bool) -> str:
        if hovered:
            return """
            QFrame#RoleCard {
                background: rgba(0,212,255,0.10);
                border-radius: 16px;
                border: 1px solid rgba(0,212,255,0.25);
            }
            QLabel {
                background: transparent;
                border: none;
            }
            """
        return """
        QFrame#RoleCard {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.03);
        }
        QLabel {
            background: transparent;
            border: none;
        }
        """

    def enterEvent(self, e):
        self._hovered = True
        self.setStyleSheet(self._style(True))
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self.setStyleSheet(self._style(False))
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if self._on_click:
            self._on_click(self.role_key)
        super().mousePressEvent(e)


# ──────────────────────────────────────────────
#  ROLE SELECTION PAGE (Page de sélection de rôle)
# ──────────────────────────────────────────────
class RoleSelectionPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background: #04080f;")

        # ── Image d'arrière-plan ──
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        IMG_PATH = os.path.join(BASE_DIR, "assets", "medical.jpg")

        self.bg = QLabel(self)
        if os.path.exists(IMG_PATH):
            pix = QPixmap(IMG_PATH)
            self.bg.setPixmap(pix)
            self.bg.setScaledContents(True)
        else:
            self.bg.setStyleSheet("background: #04080f;")

        # ── Voile sombre protecteur ──
        self.img_overlay = QFrame(self)
        self.img_overlay.setStyleSheet(
            "background: rgba(4,8,15,0.72); border:none;"
        )

        # ── Toile neuronale dynamique ──
        self.canvas = NeuralCanvas(self)

        # ── Vignette dégradée radiale ──
        self.vignette = QLabel(self)
        self.vignette.setStyleSheet("""
            background: qradialgradient(
                cx:0.5, cy:0.5, radius:0.8,
                stop:0   rgba(0,0,0,0),
                stop:1   rgba(0,0,0,0.65)
            );
        """)

        # ── Layout principal au centre ──
        self.ui = QWidget(self)
        self.ui.setStyleSheet("background:transparent;")

        center = QVBoxLayout(self.ui)
        center.setAlignment(Qt.AlignCenter)
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(0)

        # ── CARTE PRINCIPALE ──
        card = QFrame()
        card.setFixedWidth(520)
        card.setObjectName("MainCard")
        card.setStyleSheet("""
            QFrame#MainCard {
                background: rgba(8,16,32,0.88);
                border-radius: 26px;
                border: 1px solid rgba(255,255,255,0.06);
            }
        """)

        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(80)
        card_shadow.setOffset(0, 24)
        card_shadow.setColor(QColor(0, 0, 0, 160))
        card.setGraphicsEffect(card_shadow)

        card_vb = QVBoxLayout(card)
        card_vb.setContentsMargins(36, 30, 36, 36) # Marges ajustées pour le bouton retour
        card_vb.setSpacing(0)

        # ── BOUTON RETOUR (NOUVEAU) ──
        back_row = QHBoxLayout()
        back_row.setContentsMargins(0, 0, 0, 0)
        
        back_btn = QPushButton("← Retour")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                color: rgba(240, 244, 255, 0.40);
                font-size: 12px;
                font-family: 'DM Sans', 'Segoe UI', sans-serif;
                font-weight: 500;
                background: transparent;
                border: none;
                padding: 4px 0px;
                text-align: left;
            }
            QPushButton:hover {
                color: #00d4ff;
            }
        """)
        if self.main_window:
            # Connecté à la fonction de retour vers le Login de votre MainWindow
            back_btn.clicked.connect(self._handle_back)
            
        back_row.addWidget(back_btn)
        back_row.addStretch()
        card_vb.addLayout(back_row)
        card_vb.addSpacing(16)

        # ── EN-TÊTE LOGO & NOM ──
        brand_row = QHBoxLayout()
        brand_row.setAlignment(Qt.AlignCenter)
        brand_row.setSpacing(12)

        icon_box = QLabel("🧠")
        icon_box.setFixedSize(48, 48)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet("""
            font-size: 24px;
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #00d4ff, stop:1 #0066ff);
            border-radius: 13px;
        """)

        brand_name = QLabel("NeuroDetect")
        brand_name.setStyleSheet("""
            color: #f0f4ff;
            font-size: 28px;
            font-weight: 800;
            font-family: 'Syne','Segoe UI Black',sans-serif;
            background: transparent;
            letter-spacing: -0.01em;
        """)

        brand_row.addWidget(icon_box)
        brand_row.addWidget(brand_name)
        card_vb.addLayout(brand_row)
        card_vb.addSpacing(6)

        tagline = QLabel("AI Brain Tumor Detection Platform")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet("""
            color: rgba(0,212,255,0.70);
            font-size: 12px;
            font-family: 'DM Sans','Segoe UI',sans-serif;
            background: transparent;
            letter-spacing: 0.12em;
            font-weight: 300;
        """)
        card_vb.addWidget(tagline)
        card_vb.addSpacing(24)

        # — Séparateur horizontal —
        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet("background:rgba(255,255,255,0.07); border:none;")
        card_vb.addWidget(div)
        card_vb.addSpacing(24)

        # — Titre d'invitation —
        prompt = QLabel("Choisissez votre profil")
        prompt.setAlignment(Qt.AlignCenter)
        prompt.setStyleSheet("""
            color: rgba(240,244,255,0.50);
            font-size: 11px;
            font-family: 'DM Sans','Segoe UI',sans-serif;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            background: transparent;
            font-weight: 500;
        """)
        card_vb.addWidget(prompt)
        card_vb.addSpacing(14)

        # — Liste des profils cliquables —
        roles = [
            ("⚕️",  "Médecin",   "Accès au diagnostic assisté par IA",          "Médecin"),
            ("🎓",  "Étudiant",  "Apprentissage et cas cliniques interactifs",   "Étudiant"),
            ("🧑‍⚕️", "Patient",   "Suivi et résultats personnalisés",             "Patient"),
        ]

        for icon, title, desc, key in roles:
            rc = RoleCard(icon, title, desc, key, on_click=self._select_role)
            card_vb.addWidget(rc)
            card_vb.addSpacing(10)

        card_vb.addSpacing(12)

        # — Note de bas de page —
        note = QLabel("Plateforme sécurisée · Données médicales chiffrées")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet("""
            color: rgba(240,244,255,0.22);
            font-size: 10px;
            font-family: 'DM Sans','Segoe UI',sans-serif;
            background: transparent;
            letter-spacing: 0.06em;
        """)
        card_vb.addWidget(note)

        center.addWidget(card, alignment=Qt.AlignCenter)

        # ── Gestion de l'empilement des calques ──
        self.bg.lower()
        self.img_overlay.raise_()
        self.canvas.raise_()
        self.vignette.raise_()
        self.ui.raise_()

    # ── Actions ───────────────────────────────
    def _select_role(self, role_key: str):
        if self.main_window:
            self.main_window.selected_role = role_key
            self.main_window.go_register_page()

    def _handle_back(self):
        """Retourne à la page précédente (Login/Connexion)."""
        if self.main_window:
            # Cette fonction redirige vers la page de login
            if hasattr(self.main_window, "go_login"):
                self.main_window.go_login()
            elif hasattr(self.main_window, "go_login_page"):
                self.main_window.go_login_page()

    # ── Redimensionnement adaptatif ────────────
    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        for widget in (self.bg, self.img_overlay, self.canvas, self.vignette, self.ui):
            widget.setGeometry(0, 0, w, h)
        super().resizeEvent(event)