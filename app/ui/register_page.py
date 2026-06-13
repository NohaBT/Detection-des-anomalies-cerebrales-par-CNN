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
    QComboBox, QRadioButton, QScrollArea,
    QGraphicsDropShadowEffect, QButtonGroup
)
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QBrush
from PySide6.QtCore import Qt, QTimer

from database import register_user


# ══════════════════════════════════════════════
#  NEURAL CANVAS
# ══════════════════════════════════════════════
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
            {"x": random.uniform(0, w), "y": random.uniform(0, h),
             "vx": random.uniform(-0.35, 0.35), "vy": random.uniform(-0.35, 0.35),
             "r": random.uniform(1.2, 2.8), "ph": random.uniform(0, math.pi * 2)}
            for _ in range(n)
        ]

    def _step(self):
        w, h = self.width(), self.height()
        for nd in self._nodes:
            nd["x"] += nd["vx"]; nd["y"] += nd["vy"]; nd["ph"] += 0.018
            if nd["x"] < 0 or nd["x"] > w: nd["vx"] *= -1
            if nd["y"] < 0 or nd["y"] > h: nd["vy"] *= -1
        self.update()

    def resizeEvent(self, e):
        self._init_nodes(); super().resizeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for i, a in enumerate(self._nodes):
            for b in self._nodes[i+1:]:
                dx, dy = a["x"] - b["x"], a["y"] - b["y"]
                dist = math.hypot(dx, dy)
                if dist < 150:
                    pen = QPen(QColor(0, 180, 255, int((1 - dist/150)*65)))
                    pen.setWidthF(0.7); p.setPen(pen)
                    p.drawLine(int(a["x"]), int(a["y"]), int(b["x"]), int(b["y"]))
        p.setPen(Qt.NoPen)
        for nd in self._nodes:
            glow = 0.6 + 0.4 * math.sin(nd["ph"]); r = nd["r"] * glow
            p.setBrush(QBrush(QColor(0, 212, 255, int(180 * glow))))
            p.drawEllipse(int(nd["x"]-r), int(nd["y"]-r), int(r*2), int(r*2))
        p.end()


# ══════════════════════════════════════════════
#  STYLES & HELPERS
# ══════════════════════════════════════════════
FIELD_STYLE = """
QLineEdit {
    background: rgba(255,255,255,0.06); color:#f0f4ff;
    border-radius:11px; border:1px solid rgba(255,255,255,0.10);
    padding-left:14px; font-size:13px;
    font-family:'DM Sans','Segoe UI',sans-serif;
}
QLineEdit:focus {
    border:1px solid rgba(0,212,255,0.55);
    background:rgba(255,255,255,0.09);
}
QLineEdit:hover:!focus {
    border:1px solid rgba(255,255,255,0.18);
    background:rgba(255,255,255,0.08);
}
"""

COMBO_STYLE = """
QComboBox {
    background:rgba(255,255,255,0.06); color:#f0f4ff;
    border-radius:11px; border:1px solid rgba(255,255,255,0.10);
    padding-left:14px; font-size:13px;
    font-family:'DM Sans','Segoe UI',sans-serif;
}
QComboBox:hover {
    border:1px solid rgba(255,255,255,0.18);
    background:rgba(255,255,255,0.08);
}
QComboBox::drop-down { border:none; width:28px; }
QComboBox::down-arrow { image:none; }
QComboBox QAbstractItemView {
    background:#0d1a2e; color:#f0f4ff;
    border:1px solid rgba(0,212,255,0.25);
    selection-background-color:rgba(0,212,255,0.15);
    outline:none;
}
"""

RADIO_STYLE = """
QRadioButton {
    color:rgba(240,244,255,0.75); font-size:13px; spacing:8px;
    font-family:'DM Sans','Segoe UI',sans-serif;
}
QRadioButton::indicator {
    width:16px; height:16px; border-radius:8px;
    border:1px solid rgba(0,212,255,0.4);
    background:rgba(255,255,255,0.05);
}
QRadioButton::indicator:checked {
    background:#00d4ff; border:1px solid #00d4ff;
}
"""


def mk_input(placeholder, echo=QLineEdit.Normal, height=44) -> QLineEdit:
    w = QLineEdit()
    w.setPlaceholderText(placeholder)
    w.setFixedHeight(height)
    w.setEchoMode(echo)
    w.setStyleSheet(FIELD_STYLE)
    return w


def mk_label(text, size=11, color="rgba(240,244,255,0.40)", bold=False) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{color}; font-size:{size}px; font-weight:{'700' if bold else '400'};"
        f"font-family:'DM Sans','Segoe UI',sans-serif; background:transparent;"
        f"border:none; padding:0; margin:0;"
    )
    return lbl


def mk_combo(items, height=44) -> QComboBox:
    c = QComboBox(); c.addItems(items); c.setFixedHeight(height)
    c.setStyleSheet(COMBO_STYLE); return c


def mk_divider() -> QFrame:
    f = QFrame(); f.setFixedHeight(1)
    f.setStyleSheet("background:rgba(255,255,255,0.07); border:none;")
    return f


def add_full(layout, label_text, widget):
    col = QVBoxLayout(); col.setSpacing(5)
    col.addWidget(mk_label(label_text.upper(), size=10))
    col.addWidget(widget)
    layout.addLayout(col)


def add_row(layout, lbl_a, w_a, lbl_b=None, w_b=None):
    row = QHBoxLayout(); row.setSpacing(10)
    col_a = QVBoxLayout(); col_a.setSpacing(5)
    col_a.addWidget(mk_label(lbl_a.upper(), size=10)); col_a.addWidget(w_a)
    row.addLayout(col_a)
    if w_b is not None:
        col_b = QVBoxLayout(); col_b.setSpacing(5)
        col_b.addWidget(mk_label(lbl_b.upper(), size=10)); col_b.addWidget(w_b)
        row.addLayout(col_b)
    layout.addLayout(row)


# ══════════════════════════════════════════════
#  SCHOOL DATA
# ══════════════════════════════════════════════
ETABL_MEDECINE = [
    "Faculté de Médecine et de Pharmacie de Rabat (FMPR)",
    "Faculté de Médecine et de Pharmacie de Casablanca (FMPC)",
    "Faculté de Médecine et de Pharmacie de Fès (FMPF)",
    "Faculté de Médecine et de Pharmacie de Marrakech (FMPM)",
    "Faculté de Médecine et de Pharmacie d'Oujda (FMPO)",
    "Faculté de Médecine et de Pharmacie de Tanger",
    "Faculté de Médecine et de Pharmacie d'Agadir",
]
ETABL_PRIVEE = [
    "Université Internationale de Rabat — Médecine (UIR)",
    "Université Privée de Fès (UPF) — Médecine",
    "Université Mundiapolis — Sciences de la Santé",
    "Collège de Médecine du Maroc (CMM)",
    "Université Euromed de Fès — Santé",
    "ESCA École de Management — Santé (Casablanca)",
]
ETABL_INFIRMERIE = [
    "ISPITS Rabat — Institut Supérieur des Professions Infirmières",
    "ISPITS Casablanca", "ISPITS Fès", "ISPITS Marrakech",
    "ISPITS Agadir", "ISPITS Oujda", "ISPITS Tanger",
    "ISPITS Meknès", "ISPITS Béni Mellal", "ISPITS Laâyoune", "ISPITS Dakhla",
    "Institut de Formation aux Carrières de Santé (IFCS) — Rabat",
    "IFCS Casablanca", "IFCS Fès", "IFCS Marrakech",
]
ANNEES_MEDECINE_PHARMA = [
    "1ère année","2ème année","3ème année","4ème année",
    "5ème année","6ème année","Cycle de Spécialisation (Résidanat)","Master","Doctorat",
]
ANNEES_INFIRMERIE = [
    "1ère année","2ème année","3ème année",
    "Master en Sciences Infirmières","Doctorat en Sciences de la Santé",
]
ANNEES_PRIVEE = [
    "1ère année","2ème année","3ème année","4ème année",
    "5ème année","6ème année","Cycle de Spécialisation","Master","Doctorat",
]
SCHOOL_MAP = {
    "Faculté de Médecine et de Pharmacie (publique)": (ETABL_MEDECINE,   ANNEES_MEDECINE_PHARMA),
    "École privée de Médecine":                        (ETABL_PRIVEE,     ANNEES_PRIVEE),
    "ISPITS / IFCS — Infirmerie":                      (ETABL_INFIRMERIE, ANNEES_INFIRMERIE),
}

ROLE_META = {
    "Médecin": {
        "icon": "⚕️", "tag": "Espace Médecin",
        "hero": "Rejoignez\nNeuroDetect.",
        "sub":  "Plateforme de diagnostic IRM\nassistée par intelligence artificielle.",
        "features": ["Analyse IRM en temps réel","Segmentation automatique des lésions",
                     "Assistance diagnostique intelligente","Données chiffrées et conformes RGPD"],
        "badges": ["CE Médical","ISO 27001","HL7 FHIR"], "accent": "#00d4ff",
    },
    "Étudiant": {
        "icon": "🎓", "tag": "Espace Étudiant",
        "hero": "Apprenez avec\nNeuroDetect.",
        "sub":  "Cas cliniques interactifs et\napprentissage guidé par IA.",
        "features": ["Accès à des cas cliniques réels","Quiz et évaluations interactifs",
                     "Visualisation 3D des IRM","Suivi de progression personnalisé"],
        "badges": ["Accès Étudiant","Cas Cliniques","IA Pédagogique"], "accent": "#00d4ff",
    },
    "Patient": {
        "icon": "🧑‍⚕️", "tag": "Espace Patient",
        "hero": "Votre santé,\nnos priorités.",
        "sub":  "Suivez vos résultats et\ncommuniquez avec vos médecins.",
        "features": ["Accès à vos résultats d'IRM","Suivi médical personnalisé",
                     "Communication sécurisée","Historique des consultations"],
        "badges": ["Données Privées","RGPD","Sécurisé"], "accent": "#34d399",
    },
}


# ══════════════════════════════════════════════
#  ERROR / SUCCESS BANNER
# ══════════════════════════════════════════════
class ErrorBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        vb = QVBoxLayout(self); vb.setContentsMargins(14, 8, 14, 8)
        vb.addWidget(self._lbl)
        self.hide()

    def show_error(self, msg: str):
        self.setStyleSheet("QFrame{background:rgba(255,77,109,0.10);border:1px solid rgba(255,77,109,0.30);border-radius:10px;}")
        self._lbl.setStyleSheet("color:#ff4d6d;font-size:12px;background:transparent;border:none;font-family:'DM Sans','Segoe UI',sans-serif;")
        self._lbl.setText(f"⚠  {msg}"); self.show()

    def show_success(self, msg: str):
        self.setStyleSheet("QFrame{background:rgba(52,211,153,0.10);border:1px solid rgba(52,211,153,0.30);border-radius:10px;}")
        self._lbl.setStyleSheet("color:#34d399;font-size:12px;background:transparent;border:none;font-family:'DM Sans','Segoe UI',sans-serif;")
        self._lbl.setText(f"✅  {msg}"); self.show()

    def clear(self):
        self.hide(); self._lbl.setText("")


# ══════════════════════════════════════════════
#  REGISTER PAGE
# ══════════════════════════════════════════════
class RegisterPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window   = main_window
        self.selected_role = "Médecin"
        if self.main_window:
            self.selected_role = self.main_window.selected_role
        # refs to role-specific widgets (set in _build_card)
        self._radio_group   = None
        self._radio_statuts = []
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background:#04080f;")

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
        self.canvas   = NeuralCanvas(self)
        self.vignette = QLabel(self)
        self.vignette.setStyleSheet("""
            background:qradialgradient(cx:0.5,cy:0.5,radius:0.8,
                stop:0 rgba(0,0,0,0), stop:1 rgba(0,0,0,0.60));
        """)

        self.ui = QWidget(self)
        self.ui.setStyleSheet("background:transparent;")
        root = QHBoxLayout(self.ui)
        root.setContentsMargins(80, 60, 80, 60)
        root.setSpacing(0)
        root.addWidget(self._build_left(),  stretch=3)
        root.addSpacing(40)
        root.addWidget(self._build_card(),  stretch=0, alignment=Qt.AlignVCenter)

        self.bg.lower(); self.img_overlay.raise_()
        self.canvas.raise_(); self.vignette.raise_(); self.ui.raise_()

    # ── LEFT ───────────────────────────────────
    def _build_left(self) -> QWidget:
        meta   = ROLE_META.get(self.selected_role, ROLE_META["Médecin"])
        accent = meta["accent"]

        panel = QWidget(); panel.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(panel)
        vb.setAlignment(Qt.AlignVCenter | Qt.AlignLeft); vb.setSpacing(0)

        brand_row = QHBoxLayout(); brand_row.setSpacing(12)
        icon_box = QLabel("🧠"); icon_box.setFixedSize(46, 46)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet("font-size:22px;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00d4ff,stop:1 #0066ff);border-radius:12px;")
        brand_name = QLabel("NeuroDetect")
        brand_name.setStyleSheet("color:#f0f4ff;font-size:17px;font-weight:800;font-family:'Syne','Segoe UI Black',sans-serif;background:transparent;letter-spacing:0.06em;")
        brand_row.addWidget(icon_box); brand_row.addWidget(brand_name); brand_row.addStretch()
        vb.addLayout(brand_row); vb.addSpacing(34)

        role_badge = QLabel(f"{meta['icon']}  {self.selected_role}")
        role_badge.setFixedHeight(28)
        role_badge.setStyleSheet(f"color:{accent};font-size:11px;font-family:'DM Sans','Segoe UI',sans-serif;letter-spacing:0.10em;background:rgba(0,212,255,0.06);border:1px solid {accent}44;border-radius:100px;padding:4px 16px;")
        vb.addWidget(role_badge); vb.addSpacing(16)

        hero = QLabel(meta["hero"])
        hero.setStyleSheet("color:#f0f4ff;font-size:40px;font-weight:800;font-family:'Syne','Segoe UI Black',sans-serif;line-height:1.05;background:transparent;letter-spacing:-0.02em;")
        vb.addWidget(hero); vb.addSpacing(10)

        line = QFrame(); line.setFixedSize(52, 3)
        line.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {accent},stop:1 #0066ff);border-radius:2px;border:none;")
        vb.addWidget(line); vb.addSpacing(14)

        sub = mk_label(meta["sub"], size=13, color="rgba(240,244,255,0.50)")
        sub.setStyleSheet(sub.styleSheet() + " line-height:1.7; font-weight:300;")
        vb.addWidget(sub); vb.addSpacing(28)

        for feat in meta["features"]:
            row = QHBoxLayout()
            dot = QLabel(); dot.setFixedSize(7, 7)
            dot.setStyleSheet(f"background:{accent};border-radius:3px;margin-top:7px;")
            txt = mk_label(feat, size=13, color="rgba(240,244,255,0.75)")
            row.addWidget(dot, alignment=Qt.AlignTop)
            row.addSpacing(10); row.addWidget(txt); row.addStretch()
            vb.addLayout(row); vb.addSpacing(7)

        vb.addSpacing(26)
        badge_row = QHBoxLayout(); badge_row.setSpacing(8)
        for badge in meta["badges"]:
            b = QLabel(badge)
            b.setStyleSheet("color:rgba(240,244,255,0.38);font-size:10px;font-family:'DM Sans','Segoe UI',sans-serif;letter-spacing:0.08em;border:1px solid rgba(255,255,255,0.08);border-radius:100px;padding:4px 14px;background:rgba(255,255,255,0.03);")
            badge_row.addWidget(b)
        badge_row.addStretch()
        vb.addLayout(badge_row); vb.addStretch()
        return panel

    # ── CARD ───────────────────────────────────
    def _build_card(self) -> QFrame:
        meta   = ROLE_META.get(self.selected_role, ROLE_META["Médecin"])
        accent = meta["accent"]

        card = QFrame(); card.setFixedWidth(500)
        card.setStyleSheet("QFrame{background:rgba(8,16,32,0.90);border-radius:24px;border:none;}")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(80); shadow.setOffset(0, 24)
        shadow.setColor(QColor(0, 0, 0, 160)); card.setGraphicsEffect(shadow)

        vb = QVBoxLayout(card)
        vb.setContentsMargins(32, 28, 32, 28); vb.setSpacing(0)

        tag = QLabel(f"{meta['icon']}  {meta['tag']}")
        tag.setAlignment(Qt.AlignCenter); tag.setFixedHeight(28)
        tag.setStyleSheet(f"color:{accent};font-size:11px;font-family:'DM Sans','Segoe UI',sans-serif;letter-spacing:0.10em;background:rgba(0,212,255,0.08);border:1px solid {accent}55;border-radius:100px;padding:4px 18px;")
        title = QLabel("Créer un compte")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#f0f4ff;font-size:24px;font-weight:700;font-family:'Syne','Segoe UI Black',sans-serif;background:transparent;letter-spacing:-0.01em;")
        sub_lbl = mk_label("Rejoignez NeuroDetect", size=12, color="rgba(240,244,255,0.35)")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet(sub_lbl.styleSheet() + " font-weight:300;")

        vb.addWidget(tag, alignment=Qt.AlignCenter)
        vb.addSpacing(12); vb.addWidget(title)
        vb.addSpacing(3);  vb.addWidget(sub_lbl)
        vb.addSpacing(16); vb.addWidget(mk_divider()); vb.addSpacing(10)

        # ── banner ──
        self._banner = ErrorBanner()
        vb.addWidget(self._banner)
        vb.addSpacing(6)

        # ── scroll ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}QScrollBar:vertical{background:transparent;width:4px;}QScrollBar::handle:vertical{background:rgba(0,212,255,0.25);border-radius:2px;min-height:20px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        form_w = QWidget(); form_w.setStyleSheet("background:transparent;")
        fvb = QVBoxLayout(form_w); fvb.setSpacing(10); fvb.setContentsMargins(0, 0, 6, 0)

        # ── COMMON ──
        self.f_fullname = mk_input("Dr. Karim Benali" if self.selected_role == "Médecin" else "Nom complet")
        self.f_username = mk_input("nom.utilisateur")
        self.f_email    = mk_input("email@exemple.ma")
        self.f_password = mk_input("Mot de passe (8+ car., maj., chiffre, spécial)", QLineEdit.Password)
        self.f_confirm  = mk_input("Confirmer le mot de passe", QLineEdit.Password)

        for f in (self.f_fullname, self.f_username, self.f_email, self.f_password, self.f_confirm):
            f.textChanged.connect(self._banner.clear)

        add_full(fvb, "Nom complet",  self.f_fullname)
        add_row(fvb,  "Identifiant",  self.f_username, "Adresse e-mail", self.f_email)
        add_row(fvb,  "Mot de passe", self.f_password, "Confirmation",   self.f_confirm)

        fvb.addSpacing(8)
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{accent}22; border:none;")
        fvb.addWidget(sep); fvb.addSpacing(8)

        # ── MÉDECIN ──
        if self.selected_role == "Médecin":
            self.f_specialite = mk_input("Ex : Neurologie, Radiologie...")
            self.f_hopital    = mk_input("Ex : CHU Ibn Rochd, Casablanca")
            self.f_experience = mk_input("Ex : 10")
            add_row(fvb,  "Spécialité",         self.f_specialite, "Années d'expérience", self.f_experience)
            add_full(fvb, "Hôpital / Clinique", self.f_hopital)

        # ── ÉTUDIANT ──
        elif self.selected_role == "Étudiant":
            self.f_type_ecole    = mk_combo(list(SCHOOL_MAP.keys()))
            default_etabl, default_annees = list(SCHOOL_MAP.values())[0]
            self.f_etablissement = mk_combo(default_etabl)
            self.f_annee         = mk_combo(default_annees)
            self.f_filiere       = mk_input("Ex : Médecine, Pharmacie, Soins Infirmiers...")
            self.f_cne           = mk_input("CNE (optionnel)")

            add_full(fvb, "Type d'établissement", self.f_type_ecole)
            add_full(fvb, "Établissement",         self.f_etablissement)
            add_row(fvb,  "Filière",               self.f_filiere, "Année d'études", self.f_annee)
            add_full(fvb, "CNE",                   self.f_cne)

            def _update_school(idx):
                key = self.f_type_ecole.currentText()
                ecoles, annees = SCHOOL_MAP.get(key, (default_etabl, default_annees))
                self.f_etablissement.blockSignals(True); self.f_etablissement.clear()
                self.f_etablissement.addItems(ecoles); self.f_etablissement.blockSignals(False)
                self.f_annee.blockSignals(True); self.f_annee.clear()
                self.f_annee.addItems(annees); self.f_annee.blockSignals(False)

            self.f_type_ecole.currentIndexChanged.connect(_update_school)

        # ── PATIENT ──
        elif self.selected_role == "Patient":
            self.f_age    = mk_input("Ex : 35")
            self.f_ville  = mk_input("Ex : Casablanca")
            self.f_sexe   = mk_combo(["Homme", "Femme"])
            self.f_blood  = mk_combo(["A+","A−","B+","B−","AB+","AB−","O+","O−","Inconnu"])
            self.f_doctor = mk_input("Nom du médecin référent (optionnel)")

            add_row(fvb,  "Âge",             self.f_age,    "Sexe",           self.f_sexe)
            add_row(fvb,  "Ville",           self.f_ville,  "Groupe sanguin", self.f_blood)
            add_full(fvb, "Médecin référent", self.f_doctor)

            fvb.addSpacing(8)
            fvb.addWidget(mk_label("Statut médical", size=10, color="rgba(240,244,255,0.40)"))
            fvb.addSpacing(6)
            self._radio_group = QButtonGroup(form_w)
            self._radio_statuts = ["Déjà diagnostiqué(e)", "Dépistage préventif", "Suivi post-opératoire"]
            for i, (txt, checked) in enumerate([
                ("Déjà diagnostiqué(e)", False),
                ("Dépistage préventif",  True),
                ("Suivi post-opératoire",False),
            ]):
                rb = QRadioButton(txt); rb.setStyleSheet(RADIO_STYLE)
                rb.setChecked(checked); self._radio_group.addButton(rb, i)
                fvb.addWidget(rb); fvb.addSpacing(2)

        scroll.setWidget(form_w)
        vb.addWidget(scroll, stretch=1)
        vb.addSpacing(12); vb.addWidget(mk_divider()); vb.addSpacing(12)

        # ── CTA ──
        self._create_btn = QPushButton("CRÉER MON COMPTE")
        self._create_btn.setFixedHeight(50); self._create_btn.setCursor(Qt.PointingHandCursor)
        self._create_btn.setStyleSheet(f"""
            QPushButton {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {accent},stop:1 #0066ff);
                color:white; border:none; border-radius:12px; font-size:13px; font-weight:700;
                font-family:'Syne','Segoe UI Black',sans-serif; letter-spacing:0.12em;
            }}
            QPushButton:hover {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33ddff,stop:1 #2288ff);
            }}
            QPushButton:pressed {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00aacc,stop:1 #0044cc);
            }}
            QPushButton:disabled {{
                background:rgba(255,255,255,0.08); color:rgba(255,255,255,0.30);
            }}
        """)
        self._create_btn.clicked.connect(self._handle_register)
        vb.addWidget(self._create_btn); vb.addSpacing(8)

        back_btn = QPushButton("← Retour à la sélection")
        back_btn.setFixedHeight(42); back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.04);color:rgba(240,244,255,0.55);border:1px solid rgba(255,255,255,0.08);border-radius:12px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;}QPushButton:hover{background:rgba(255,255,255,0.08);color:#f0f4ff;border:1px solid rgba(255,255,255,0.15);}")
        if self.main_window:
            back_btn.clicked.connect(self.main_window.go_login_page)
        vb.addWidget(back_btn); vb.addSpacing(10)

        login_btn = QPushButton("Déjà inscrit ? Se connecter →")
        login_btn.setFlat(True); login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet(f"QPushButton{{background:transparent;color:{accent};border:none;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;}}QPushButton:hover{{color:#f0f4ff;}}")
        if self.main_window:
            login_btn.clicked.connect(self.main_window.go_login)
        vb.addWidget(login_btn, alignment=Qt.AlignCenter)

        return card

    # ── REGISTER HANDLER ───────────────────────
    def _handle_register(self):
        self._banner.clear()
        role = self.selected_role

        fullname = self.f_fullname.text().strip()
        username = self.f_username.text().strip()
        email    = self.f_email.text().strip()
        password = self.f_password.text()
        confirm  = self.f_confirm.text()

        extra = {}
        if role == "Médecin":
            extra = {
                "specialite": self.f_specialite.text().strip(),
                "hopital":    self.f_hopital.text().strip(),
                "experience": self.f_experience.text().strip(),
            }
        elif role == "Étudiant":
            extra = {
                "type_ecole":    self.f_type_ecole.currentText(),
                "etablissement": self.f_etablissement.currentText(),
                "filiere":       self.f_filiere.text().strip(),
                "annee_etude":   self.f_annee.currentText(),
                "cne":           self.f_cne.text().strip(),
            }
        elif role == "Patient":
            statut = ""
            if self._radio_group:
                sel = self._radio_group.checkedId()
                if 0 <= sel < len(self._radio_statuts):
                    statut = self._radio_statuts[sel]
            extra = {
                "age":              self.f_age.text().strip(),
                "sexe":             self.f_sexe.currentText(),
                "ville":            self.f_ville.text().strip(),
                "groupe_sanguin":   self.f_blood.currentText(),
                "medecin_referent": self.f_doctor.text().strip(),
                "statut_medical":   statut,
            }

        self._create_btn.setEnabled(False)
        self._create_btn.setText("Inscription...")

        success, msg = register_user(fullname, username, email, password, confirm, role, extra)

        self._create_btn.setEnabled(True)
        self._create_btn.setText("CRÉER MON COMPTE")

        if not success:
            self._banner.show_error(msg)
            return

        self._banner.show_success("Compte créé avec succès ! Redirection vers la connexion...")
        QTimer.singleShot(1800, self._go_login)

    def _go_login(self):
        if self.main_window:
            self.main_window.go_login()

    # ── resize ────────────────────────────────
    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        for widget in (self.bg, self.img_overlay, self.canvas, self.vignette, self.ui):
            widget.setGeometry(0, 0, w, h)
        super().resizeEvent(event)