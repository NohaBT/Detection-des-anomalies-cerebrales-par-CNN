"""
patient_dashboard.py  —  connecté à database.py + current_user
"""
import os, sys, math, random

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFrame,
    QVBoxLayout, QHBoxLayout, QScrollArea,
    QGraphicsDropShadowEffect, QProgressBar
)
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QBrush
from PySide6.QtCore import Qt, QTimer

from database import _get_connection


# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════
def mk_label(text, size=12, color="#f0f4ff", bold=False,
             family="'DM Sans','Segoe UI',sans-serif") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{color}; font-size:{size}px; font-weight:{'700' if bold else '400'};"
        f"font-family:{family}; background:transparent; border:none;"
    )
    lbl.setWordWrap(True)
    return lbl

def mk_divider() -> QFrame:
    f = QFrame(); f.setFixedHeight(1)
    f.setStyleSheet("background:rgba(255,255,255,0.07); border:none;")
    return f

def mk_card(radius=16) -> QFrame:
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:rgba(8,16,32,0.88);border-radius:{radius}px;border:1px solid rgba(255,255,255,0.07);}}")
    sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(24)
    sh.setOffset(0, 6); sh.setColor(QColor(0, 0, 0, 70))
    f.setGraphicsEffect(sh)
    return f


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

    def _init_nodes(self, n=50):
        w = max(self.width(), 1600)
        h = max(self.height(), 900)
        self._nodes = [{"x": random.uniform(0,w), "y": random.uniform(0,h),
            "vx": random.uniform(-0.3,0.3), "vy": random.uniform(-0.3,0.3),
            "r": random.uniform(1,2.5), "ph": random.uniform(0, math.pi*2)}
            for _ in range(n)]

    def _step(self):
        w, h = self.width(), self.height()
        for n in self._nodes:
            n["x"]+=n["vx"]; n["y"]+=n["vy"]; n["ph"]+=0.018
            if n["x"]<0 or n["x"]>w: n["vx"]*=-1
            if n["y"]<0 or n["y"]>h: n["vy"]*=-1
        self.update()

    def resizeEvent(self, e): 
            self._init_nodes()
            super().resizeEvent(e)
            
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        for i, a in enumerate(self._nodes):
            for b in self._nodes[i+1:]:
                dx, dy = a["x"] - b["x"], a["y"] - b["y"]
                dist = math.hypot(dx, dy)
                if dist < 140:
                    pen = QPen(QColor(52,211,153, int((1-dist/140)*55))); pen.setWidthF(0.6)
                    p.setPen(pen)
                    p.drawLine(int(a["x"]),int(a["y"]),int(b["x"]),int(b["y"]))
        p.setPen(Qt.NoPen)
        for n in self._nodes:
            g = 0.6+0.4*math.sin(n["ph"]); r = n["r"]*g
            p.setBrush(QBrush(QColor(52,211,153, int(150*g))))
            p.drawEllipse(int(n["x"]-r),int(n["y"]-r),int(r*2),int(r*2))
        p.end()


# ══════════════════════════════════════════════
#  DB HELPERS
# ══════════════════════════════════════════════
def get_patient_info(user_id: int) -> dict:
    try:
        with _get_connection() as conn:
            row = conn.execute("""
                SELECT u.fullname, u.email, u.created_at,
                       p.age, p.sexe, p.ville, p.groupe_sanguin,
                       p.medecin_referent, p.statut_medical
                FROM users u
                LEFT JOIN patients p ON p.user_id = u.id
                WHERE u.id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else {}
    except Exception:
        return {}

def get_patient_analyses(user_id: int) -> list:
    """Récupère les analyses liées au patient via son médecin référent (nom)."""
    try:
        with _get_connection() as conn:
            # chercher par patient_nom (fullname) dans analyses
            info = get_patient_info(user_id)
            fullname = info.get("fullname", "")
            rows = conn.execute("""
                SELECT * FROM analyses
                WHERE patient_nom LIKE ?
                ORDER BY date_analyse DESC
            """, (f"%{fullname}%",)).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []

def get_medecin_by_name(nom: str) -> dict:
    try:
        with _get_connection() as conn:
            row = conn.execute("""
                SELECT u.fullname, u.email, m.specialite, m.hopital
                FROM users u
                JOIN medecins m ON m.user_id = u.id
                WHERE u.fullname LIKE ?
                LIMIT 1
            """, (f"%{nom}%",)).fetchone()
            return dict(row) if row else {}
    except Exception:
        return {}


# ══════════════════════════════════════════════
#  PATIENT DASHBOARD
# ══════════════════════════════════════════════
class PatientDashboardPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._user       = {}
        self._patient    = {}
        if main_window and hasattr(main_window, "current_user") and main_window.current_user:
            u = main_window.current_user
            self._user    = u
            self._patient = {
                "age":              u.get("age", "—"),
                "sexe":             u.get("sexe", "—"),
                "ville":            u.get("ville", "—"),
                "groupe_sanguin":   u.get("groupe_sanguin", "—"),
                "medecin_referent": u.get("medecin_referent", "—"),
                "statut_medical":   u.get("statut_medical", "—"),
            }
        self._build_ui()

    def _build_ui(self):
            self.setStyleSheet("background:#04080f;")
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            IMG_PATH = os.path.join(BASE_DIR, "assets", "medical.jpg")
            
            self.bg = QLabel(self)
            if os.path.exists(IMG_PATH):
                self.bg.setPixmap(QPixmap(IMG_PATH))
                self.bg.setScaledContents(True)
                
            self.overlay = QFrame(self)
            self.overlay.setStyleSheet("background:rgba(4,8,15,0.85); border:none;")
            
            self.canvas = NeuralCanvas(self)

            self.ui = QWidget(self)
            self.ui.setStyleSheet("background:transparent;")
            
            root = QHBoxLayout(self.ui)
            root.setContentsMargins(0,0,0,0)
            root.setSpacing(0)
            root.addWidget(self._build_sidebar())
            root.addWidget(self._build_content(), stretch=1)

            self.bg.lower()
            self.overlay.raise_()
            self.canvas.raise_()
            self.ui.raise_()

    # ── SIDEBAR ────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sb = QWidget(); sb.setFixedWidth(220)
        sb.setStyleSheet("QWidget{background:rgba(6,12,24,0.95);border-right:1px solid rgba(255,255,255,0.06);}")
        vb = QVBoxLayout(sb); vb.setContentsMargins(16,28,16,20); vb.setSpacing(6)

        icon_b = QLabel("🧠"); icon_b.setFixedSize(34,34); icon_b.setAlignment(Qt.AlignCenter)
        icon_b.setStyleSheet("font-size:16px;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #34d399,stop:1 #059669);border-radius:9px;border:none;")
        bname = mk_label("NeuroDetect", 14, "#f0f4ff", True, "'Syne','Segoe UI Black',sans-serif")
        br = QHBoxLayout(); br.setSpacing(10)
        br.addWidget(icon_b); br.addWidget(bname); br.addStretch()
        vb.addLayout(br); vb.addSpacing(10)

        # patient card avec vraies infos
        fullname = self._user.get("fullname", "Patient")
        age      = self._patient.get("age", "—")
        sexe     = self._patient.get("sexe", "—")

        pc = QFrame()
        pc.setStyleSheet("QFrame{background:rgba(52,211,153,0.06);border-radius:12px;border:1px solid rgba(52,211,153,0.15);}")
        pc_vb = QVBoxLayout(pc); pc_vb.setContentsMargins(12,10,12,10); pc_vb.setSpacing(2)
        pc_vb.addWidget(mk_label(f"🧑‍⚕️  {fullname}", 12, "#f0f4ff", True))
        pc_vb.addWidget(mk_label(f"Patient · {age} ans · {sexe}", 10, "rgba(240,244,255,0.40)"))
        vb.addWidget(pc); vb.addSpacing(16)

        vb.addWidget(mk_label("MENU", 9, "rgba(240,244,255,0.25)"))
        vb.addSpacing(6)

        for label in ["📋  Mes résultats", "👨‍⚕️  Mon médecin", "📅  Mon profil"]:
            btn = QPushButton(label); btn.setFixedHeight(44)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("QPushButton{background:transparent;color:rgba(240,244,255,0.55);border:none;border-radius:12px;font-size:13px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:14px;}QPushButton:hover{background:rgba(255,255,255,0.05);color:rgba(240,244,255,0.85);}")
            vb.addWidget(btn)

        vb.addStretch(); vb.addWidget(mk_divider()); vb.addSpacing(8)
        logout = QPushButton("⎋  Déconnexion"); logout.setFixedHeight(42)
        logout.setCursor(Qt.PointingHandCursor)
        logout.setStyleSheet("QPushButton{background:rgba(255,77,109,0.08);color:rgba(255,77,109,0.80);border:1px solid rgba(255,77,109,0.15);border-radius:12px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:14px;}QPushButton:hover{background:rgba(255,77,109,0.15);color:#ff4d6d;}")
        if self.main_window: logout.clicked.connect(self.main_window.go_login)
        vb.addWidget(logout)
        return sb

    # ── CONTENT ────────────────────────────────
    def _build_content(self) -> QWidget:
        w = QWidget(); w.setStyleSheet("background:transparent;")
        sv = QScrollArea(); sv.setWidgetResizable(True)
        sv.setFrameShape(QFrame.NoFrame)
        sv.setStyleSheet("QScrollArea{background:transparent;border:none;}QScrollBar:vertical{width:4px;background:transparent;}QScrollBar::handle:vertical{background:rgba(52,211,153,0.25);border-radius:2px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        sv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(inner); vb.setContentsMargins(28,24,28,24); vb.setSpacing(18)

        fullname = self._user.get("fullname", "Patient")
        first    = fullname.split()[0] if fullname else "Patient"

        vb.addWidget(mk_label(f"Bonjour, {first} 👋", 22, "#f0f4ff", True,
                               "'Syne','Segoe UI Black',sans-serif"))
        vb.addWidget(mk_label("Voici un résumé de votre dossier médical.",
                               12, "rgba(240,244,255,0.45)"))
        vb.addWidget(mk_divider())

        # ── STATUT MÉDICAL ──
        status_card = mk_card()
        sc_vb = QVBoxLayout(status_card); sc_vb.setContentsMargins(22,18,22,18); sc_vb.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.addWidget(mk_label("🩺  Statut médical actuel", 13, "#f0f4ff", True))
        top_row.addStretch()
        statut = self._patient.get("statut_medical", "—")
        badge = QLabel(statut if statut != "—" else "Non renseigné")
        badge.setFixedHeight(24)
        badge.setStyleSheet("color:#34d399;font-size:10px;letter-spacing:0.08em;background:rgba(52,211,153,0.10);border:1px solid rgba(52,211,153,0.25);border-radius:100px;padding:2px 12px;font-family:'DM Sans','Segoe UI',sans-serif;")
        top_row.addWidget(badge)
        sc_vb.addLayout(top_row)
        sc_vb.addWidget(mk_divider())

        info_grid = QHBoxLayout(); info_grid.setSpacing(0)
        patient_info = [
            ("Âge",           self._patient.get("age",            "—")),
            ("Sexe",          self._patient.get("sexe",           "—")),
            ("Groupe sanguin",self._patient.get("groupe_sanguin", "—")),
            ("Ville",         self._patient.get("ville",          "—")),
        ]
        for i, (k, v) in enumerate(patient_info):
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(mk_label(k, 10, "rgba(240,244,255,0.38)"))
            col.addWidget(mk_label(str(v) if v else "—", 13, "#f0f4ff", True))
            info_grid.addLayout(col)
            if i < len(patient_info)-1:
                sep = QFrame(); sep.setFixedWidth(1)
                sep.setStyleSheet("background:rgba(255,255,255,0.07);border:none;")
                info_grid.addSpacing(20); info_grid.addWidget(sep); info_grid.addSpacing(20)
        sc_vb.addLayout(info_grid)
        vb.addWidget(status_card)

        # ── RÉSULTATS IRM depuis DB ──
        vb.addWidget(mk_label("Mes résultats IRM", 16, "#f0f4ff", True,
                               "'Syne','Segoe UI Black',sans-serif"))

        user_id  = self._user.get("id")
        analyses = get_patient_analyses(user_id) if user_id else []

        if analyses:
            for row_data in analyses[:5]:  # max 5
                date_str = str(row_data.get("date_analyse","—"))[:16]
                typ      = row_data.get("type_tumeur", "—")
                res      = row_data.get("resultat",    "—")
                conf     = row_data.get("confiance",   0)
                conf_pct = round(conf * 100) if conf else 0
                detected = res not in ("—","Aucune tumeur","notumor","")

                rc = mk_card(12)
                r_vb = QVBoxLayout(rc); r_vb.setContentsMargins(18,14,18,14); r_vb.setSpacing(10)

                top = QHBoxLayout()
                top.addWidget(mk_label(f"📅  {date_str}", 11, "rgba(240,244,255,0.40)"))
                top.addSpacing(12)
                top.addWidget(mk_label("IRM Cérébrale", 12, "#f0f4ff", True))
                top.addStretch()
                col_b = "#ff4d6d" if detected else "#34d399"
                res_badge = QLabel("Positif" if detected else "Négatif")
                res_badge.setStyleSheet(f"color:{col_b};font-size:10px;background:rgba(0,0,0,0.2);border:1px solid {col_b}44;border-radius:100px;padding:2px 12px;font-family:'DM Sans','Segoe UI',sans-serif;")
                top.addWidget(res_badge)
                r_vb.addLayout(top)

                r_vb.addWidget(mk_label(f"Type détecté : {typ}" if detected else "Aucune tumeur détectée",
                                         12, "rgba(240,244,255,0.65)"))

                if conf_pct > 0:
                    conf_row = QHBoxLayout()
                    conf_row.addWidget(mk_label(f"Confiance IA : {conf_pct}%", 11, "rgba(240,244,255,0.40)"))
                    conf_row.addStretch()
                    bar = QProgressBar(); bar.setValue(conf_pct); bar.setFixedHeight(5)
                    bar.setTextVisible(False); bar.setFixedWidth(120)
                    bar.setStyleSheet(f"QProgressBar{{background:rgba(255,255,255,0.08);border-radius:3px;border:none;}}QProgressBar::chunk{{background:{col_b};border-radius:3px;}}")
                    conf_row.addWidget(bar)
                    r_vb.addLayout(conf_row)

                vb.addWidget(rc)
        else:
            empty = mk_card(12)
            ev = QVBoxLayout(empty); ev.setContentsMargins(20, 20, 20, 20)
            ev.addWidget(mk_label("Aucune analyse IRM enregistrée pour le moment.",
                                   13, "rgba(240,244,255,0.35)"))
            ev.addWidget(mk_label("Votre médecin peut effectuer une analyse IRM via la plateforme.",
                                   11, "rgba(240,244,255,0.25)"))
            vb.addWidget(empty)

        # ── MÉDECIN RÉFÉRENT ──
        vb.addWidget(mk_label("Mon médecin référent", 16, "#f0f4ff", True,
                               "'Syne','Segoe UI Black',sans-serif"))

        ref_nom = self._patient.get("medecin_referent", "")
        doc_info = get_medecin_by_name(ref_nom) if ref_nom and ref_nom != "—" else {}

        doc_card = mk_card()
        d_vb = QVBoxLayout(doc_card); d_vb.setContentsMargins(22,18,22,18); d_vb.setSpacing(12)
        doc_row = QHBoxLayout(); doc_row.setSpacing(16)
        avatar = QLabel("⚕️"); avatar.setFixedSize(52,52); avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("font-size:26px;background:rgba(0,212,255,0.10);border:1px solid rgba(0,212,255,0.20);border-radius:26px;")

        doc_info_col = QVBoxLayout(); doc_info_col.setSpacing(3)
        doc_name  = doc_info.get("fullname",  ref_nom if ref_nom and ref_nom != "—" else "Non renseigné")
        doc_spec  = doc_info.get("specialite","—")
        doc_hopit = doc_info.get("hopital",   "—")
        doc_email = doc_info.get("email",     "—")

        doc_info_col.addWidget(mk_label(doc_name, 14, "#f0f4ff", True))
        if doc_spec != "—":
            doc_info_col.addWidget(mk_label(f"{doc_spec} · {doc_hopit}", 11, "rgba(240,244,255,0.45)"))
        if doc_email != "—":
            doc_info_col.addWidget(mk_label(f"✉️  {doc_email}", 11, "rgba(240,244,255,0.35)"))

        doc_row.addWidget(avatar, alignment=Qt.AlignTop)
        doc_row.addLayout(doc_info_col); doc_row.addStretch()
        d_vb.addLayout(doc_row)
        vb.addWidget(doc_card)
        vb.addStretch()

        sv.setWidget(inner)
        outer = QVBoxLayout(w); outer.setContentsMargins(0,0,0,0); outer.addWidget(sv)
        return w

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        if hasattr(self, 'bg'): self.bg.setGeometry(0, 0, w, h)
        if hasattr(self, 'overlay'): self.overlay.setGeometry(0, 0, w, h)
        if hasattr(self, 'canvas'): self.canvas.setGeometry(0, 0, w, h)
        if hasattr(self, 'ui'): self.ui.setGeometry(0, 0, w, h)
        
        super().resizeEvent(event)