"""
student_dashboard.py  —  Dashboard Étudiant — données réelles uniquement
"""
import os, sys, math, random

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFrame,
    QVBoxLayout, QHBoxLayout, QScrollArea,
    QGraphicsDropShadowEffect, QProgressBar,
    QStackedWidget, QGridLayout
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
    f.setStyleSheet(f"QFrame{{background:rgba(8,16,32,0.88);border-radius:{radius}px;"
                    f"border:1px solid rgba(255,255,255,0.07);}}")
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(24); sh.setOffset(0, 6); sh.setColor(QColor(0, 0, 0, 70))
    f.setGraphicsEffect(sh)
    return f

def mk_empty_state(icon: str, title: str, sub: str) -> QFrame:
    """Carte état vide générique."""
    card = mk_card(14)
    vb = QVBoxLayout(card); vb.setContentsMargins(24, 32, 24, 32)
    vb.setSpacing(8); vb.setAlignment(Qt.AlignCenter)
    ic = QLabel(icon); ic.setAlignment(Qt.AlignCenter)
    ic.setStyleSheet("font-size:36px; background:transparent; border:none;")
    vb.addWidget(ic)
    vb.addWidget(mk_label(title, 14, "#f0f4ff", True))
    vb.addWidget(mk_label(sub,   12, "rgba(240,244,255,0.35)"))
    return card

def mk_scroll() -> QScrollArea:
    sv = QScrollArea(); sv.setWidgetResizable(True); sv.setFrameShape(QFrame.NoFrame)
    sv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    sv.setStyleSheet("""
        QScrollArea { background:transparent; border:none; }
        QScrollBar:vertical { background:transparent; width:4px; }
        QScrollBar::handle:vertical {
            background:rgba(167,139,250,0.25); border-radius:2px; min-height:20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
    """)
    return sv


# ══════════════════════════════════════════════
#  NAV BUTTON
# ══════════════════════════════════════════════
class NavBtn(QPushButton):
    def __init__(self, icon, label, active=False, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon}  {label}")
        self.setFixedHeight(46); self.setCursor(Qt.PointingHandCursor)
        self._active = active; self._apply()

    def set_active(self, v): self._active = v; self._apply()

    def _apply(self):
        if self._active:
            self.setStyleSheet("""
                QPushButton { background:rgba(167,139,250,0.12); color:#a78bfa;
                    border:none; border-radius:12px; font-size:13px; font-weight:600;
                    font-family:'DM Sans','Segoe UI',sans-serif;
                    text-align:left; padding-left:14px; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton { background:transparent; color:rgba(240,244,255,0.55);
                    border:none; border-radius:12px; font-size:13px;
                    font-family:'DM Sans','Segoe UI',sans-serif;
                    text-align:left; padding-left:14px; }
                QPushButton:hover { background:rgba(255,255,255,0.05);
                    color:rgba(240,244,255,0.85); }
            """)


# ══════════════════════════════════════════════
#  DB HELPERS
# ══════════════════════════════════════════════
def get_etudiant_info(user_id: int) -> dict:
    try:
        with _get_connection() as conn:
            row = conn.execute("""
                SELECT u.fullname, u.email, u.created_at,
                       e.type_ecole, e.etablissement, e.filiere,
                       e.annee_etude, e.cne
                FROM users u
                LEFT JOIN etudiants e ON e.user_id = u.id
                WHERE u.id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else {}
    except Exception:
        return {}

def get_real_cases() -> list:
    """Cas cliniques réels depuis la DB (anonymisés)."""
    try:
        with _get_connection() as conn:
            rows = conn.execute("""
                SELECT type_tumeur, localisation, grade,
                       confiance, date_analyse, resultat
                FROM analyses
                WHERE resultat IS NOT NULL AND resultat != ''
                ORDER BY date_analyse DESC
                LIMIT 20
            """).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []

def get_total_analyses() -> int:
    try:
        with _get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM analyses").fetchone()
            return row["cnt"] if row else 0
    except Exception:
        return 0


# ══════════════════════════════════════════════
#  PAGE : CAS CLINIQUES
# ══════════════════════════════════════════════
def build_cas_cliniques() -> QWidget:
    page = QWidget(); page.setStyleSheet("background:transparent;")
    sv = mk_scroll()

    inner = QWidget(); inner.setStyleSheet("background:transparent;")
    vb = QVBoxLayout(inner); vb.setContentsMargins(28, 24, 28, 24); vb.setSpacing(16)

    # header
    vb.addWidget(mk_label("Cas Cliniques", 20, "#f0f4ff", True,
                           "'Syne','Segoe UI Black',sans-serif"))
    vb.addWidget(mk_label(
        "Cas IRM réels analysés par le modèle NeuroDetect — anonymisés à des fins pédagogiques.",
        12, "rgba(240,244,255,0.45)"
    ))
    vb.addWidget(mk_divider())

    cases  = get_real_cases()
    total  = get_total_analyses()

    if not cases:
        # état vide
        vb.addSpacing(20)
        vb.addWidget(mk_empty_state(
            "🔬",
            "Aucun cas disponible pour le moment",
            "Les cas cliniques apparaîtront ici dès que des médecins\n"
            "auront effectué des analyses IRM sur la plateforme."
        ))
    else:
        # compteur
        info_bar = QFrame()
        info_bar.setStyleSheet("""
            QFrame { background:rgba(167,139,250,0.08); border-radius:10px;
                border:1px solid rgba(167,139,250,0.20); }
        """)
        ib_vb = QVBoxLayout(info_bar); ib_vb.setContentsMargins(14, 10, 14, 10)
        ib_vb.addWidget(mk_label(
            f"📊  {total} analyse(s) disponible(s) · {len(cases)} cas affichés",
            12, "#a78bfa"
        ))
        vb.addWidget(info_bar)

        CLASS_COLORS = {
            "Gliome":              "#ff4d6d",
            "glioma":              "#ff4d6d",
            "Méningiome":          "#fbbf24",
            "meningioma":          "#fbbf24",
            "Tumeur hypophysaire": "#a78bfa",
            "pituitary":           "#a78bfa",
            "Aucune tumeur":       "#34d399",
            "notumor":             "#34d399",
        }
        NIVEAU_MAP = {
            "Gliome":              ("Avancé",        "#ff4d6d"),
            "glioma":              ("Avancé",        "#ff4d6d"),
            "Méningiome":          ("Intermédiaire", "#fbbf24"),
            "meningioma":          ("Intermédiaire", "#fbbf24"),
            "Tumeur hypophysaire": ("Intermédiaire", "#fbbf24"),
            "pituitary":           ("Intermédiaire", "#fbbf24"),
            "Aucune tumeur":       ("Débutant",      "#34d399"),
            "notumor":             ("Débutant",      "#34d399"),
        }

        for i, case in enumerate(cases):
            res      = case.get("resultat") or "—"
            typ      = case.get("type_tumeur") or "—"
            loc      = case.get("localisation") or "—"
            grade    = case.get("grade") or "—"
            conf     = case.get("confiance")
            conf_pct = round(conf * 100) if conf is not None else 0
            date_str = str(case.get("date_analyse") or "—")[:10]

            col            = CLASS_COLORS.get(res, "#00d4ff")
            niveau, niv_col = NIVEAU_MAP.get(res, ("—", "#00d4ff"))

            card = mk_card(14)
            cvb  = QVBoxLayout(card)
            cvb.setContentsMargins(20, 16, 20, 16); cvb.setSpacing(10)

            # titre row
            top = QHBoxLayout()
            top.addWidget(mk_label(f"Cas #{i+1} — {res}", 14, "#f0f4ff", True))
            top.addStretch()
            niv_lbl = QLabel(niveau); niv_lbl.setFixedHeight(22)
            niv_lbl.setStyleSheet(f"""
                color:{niv_col}; font-size:10px; background:rgba(0,0,0,0.2);
                border:1px solid {niv_col}44; border-radius:100px;
                padding:2px 12px; font-family:'DM Sans','Segoe UI',sans-serif;
            """)
            top.addWidget(niv_lbl)
            cvb.addLayout(top)

            # infos médicales
            info_row = QHBoxLayout(); info_row.setSpacing(0)
            for j, (k, v) in enumerate([("Type", typ), ("Localisation", loc),
                                          ("Grade", grade), ("Date", date_str)]):
                ic = QVBoxLayout(); ic.setSpacing(2)
                ic.addWidget(mk_label(k, 10, "rgba(240,244,255,0.35)"))
                ic.addWidget(mk_label(v, 12, "rgba(240,244,255,0.75)", True))
                info_row.addLayout(ic)
                if j < 3:
                    sep = QFrame(); sep.setFixedWidth(1)
                    sep.setStyleSheet("background:rgba(255,255,255,0.07);border:none;")
                    info_row.addSpacing(16); info_row.addWidget(sep); info_row.addSpacing(16)
            cvb.addLayout(info_row)

            # barre confiance IA
            if conf_pct > 0:
                cr = QHBoxLayout()
                cr.addWidget(mk_label(f"Confiance IA", 10, "rgba(240,244,255,0.35)"))
                cbar = QProgressBar(); cbar.setValue(conf_pct)
                cbar.setFixedHeight(5); cbar.setTextVisible(False)
                cbar.setStyleSheet(f"""
                    QProgressBar {{ background:rgba(255,255,255,0.07);
                        border-radius:3px; border:none; }}
                    QProgressBar::chunk {{ background:{col}; border-radius:3px; }}
                """)
                cr.addSpacing(10); cr.addWidget(cbar)
                cr.addSpacing(8)
                cr.addWidget(mk_label(f"{conf_pct}%", 11, col, True))
                cvb.addLayout(cr)

            vb.addWidget(card)

    vb.addStretch()
    sv.setWidget(inner)

    out = QWidget(); out.setStyleSheet("background:transparent;")
    QVBoxLayout(out).addWidget(sv)
    QVBoxLayout(out).setContentsMargins(0, 0, 0, 0)
    return out


# ══════════════════════════════════════════════
#  PAGE : QUIZ  (basé sur le vrai modèle)
# ══════════════════════════════════════════════
def build_quiz_page() -> QWidget:
    page = QWidget(); page.setStyleSheet("background:transparent;")
    sv = mk_scroll()

    inner = QWidget(); inner.setStyleSheet("background:transparent;")
    vb = QVBoxLayout(inner); vb.setContentsMargins(28, 24, 28, 24); vb.setSpacing(16)

    vb.addWidget(mk_label("Quiz & Évaluations", 20, "#f0f4ff", True,
                           "'Syne','Segoe UI Black',sans-serif"))
    vb.addWidget(mk_label(
        "Questions basées sur le modèle IA NeuroDetect et la neuro-oncologie.",
        12, "rgba(240,244,255,0.45)"
    ))
    vb.addWidget(mk_divider())

    QUIZZES = [
        {
            "question": "Quelles sont les 4 classes classifiées par le modèle NeuroDetect ?",
            "choices": [
                ("A", "Gliome, Méningiome, Lymphome, Épendymome",             False),
                ("B", "Gliome, Méningiome, Tumeur hypophysaire, Pas de tumeur",True),
                ("C", "Gliome, Astrocytome, Métastase, Pas de tumeur",        False),
                ("D", "Méningiome, GBM, Schwannome, Pas de tumeur",           False),
            ],
            "explication": "Le modèle MobileNetV2 de NeuroDetect est entraîné sur 4 classes : glioma, meningioma, pituitary (tumeur hypophysaire) et notumor."
        },
        {
            "question": "Quelle est la taille d'entrée des images IRM pour le modèle NeuroDetect ?",
            "choices": [
                ("A", "128 × 128 px", False),
                ("B", "256 × 256 px", False),
                ("C", "224 × 224 px", True),
                ("D", "512 × 512 px", False),
            ],
            "explication": "MobileNetV2 utilise une entrée de 224×224 pixels en RGB, normalisée entre 0 et 1 (divisée par 255)."
        },
        {
            "question": "Le Glioblastome Multiforme (GBM) correspond à quel grade OMS ?",
            "choices": [
                ("A", "Grade I",  False),
                ("B", "Grade II", False),
                ("C", "Grade III",False),
                ("D", "Grade IV", True),
            ],
            "explication": "Le GBM est la tumeur cérébrale primitive la plus agressive — grade IV OMS. Survie médiane ~15 mois avec le protocole Stupp."
        },
        {
            "question": "Quelle normalisation est appliquée aux images avant la prédiction ?",
            "choices": [
                ("A", "Standardisation Z-score (mean=0, std=1)", False),
                ("B", "Division par 255 → valeurs entre 0 et 1", True),
                ("C", "Min-Max sur chaque image",                False),
                ("D", "Aucune normalisation",                    False),
            ],
            "explication": "Le preprocessing applique img / 255.0 après conversion BGR→RGB et redimensionnement en 224×224."
        },
        {
            "question": "Où se localise typiquement l'adénome hypophysaire ?",
            "choices": [
                ("A", "Lobe frontal",                 False),
                ("B", "Cervelet",                     False),
                ("C", "Selle turcique (hypophyse)",   True),
                ("D", "Méninges pariétales",           False),
            ],
            "explication": "L'adénome hypophysaire se développe dans la glande hypophysaire, logée dans la selle turcique à la base du crâne."
        },
    ]

    _state = {"current": 0, "score": 0, "answered": [None] * len(QUIZZES)}

    quiz_card = mk_card()
    qvb = QVBoxLayout(quiz_card); qvb.setContentsMargins(22, 18, 22, 18); qvb.setSpacing(12)

    header_row = QHBoxLayout()
    q_counter  = mk_label(f"Q 1 / {len(QUIZZES)}", 11, "rgba(240,244,255,0.40)")
    score_lbl  = mk_label("Score : 0 / 0", 11, "#a78bfa", True)
    header_row.addWidget(mk_label("🎯  Quiz NeuroDetect", 13, "#a78bfa", True))
    header_row.addStretch()
    header_row.addWidget(q_counter); header_row.addSpacing(12)
    header_row.addWidget(score_lbl)
    qvb.addLayout(header_row)
    qvb.addWidget(mk_divider())

    question_lbl = mk_label("", 13, "#f0f4ff")
    qvb.addWidget(question_lbl)

    choice_btns = []
    for _ in range(4):
        btn = QPushButton(); btn.setFixedHeight(46); btn.setCursor(Qt.PointingHandCursor)
        qvb.addWidget(btn); choice_btns.append(btn)

    expl_lbl = mk_label("", 12, "rgba(240,244,255,0.55)")
    expl_lbl.hide(); qvb.addWidget(expl_lbl)

    next_btn = QPushButton("Question suivante →")
    next_btn.setFixedHeight(38); next_btn.setCursor(Qt.PointingHandCursor); next_btn.hide()
    next_btn.setStyleSheet("""
        QPushButton { background:rgba(167,139,250,0.12); color:#a78bfa;
            border:1px solid rgba(167,139,250,0.25); border-radius:10px;
            font-size:12px; font-family:'DM Sans','Segoe UI',sans-serif; padding:0 16px; }
        QPushButton:hover { background:rgba(167,139,250,0.22); }
    """)
    qvb.addWidget(next_btn, alignment=Qt.AlignRight)

    retry_btn = QPushButton("Recommencer le Quiz ↺")
    retry_btn.setFixedHeight(38); retry_btn.setCursor(Qt.PointingHandCursor); retry_btn.hide()
    retry_btn.setStyleSheet("""
        QPushButton { background:rgba(52,211,153,0.12); color:#34d399;
            border:1px solid rgba(52,211,153,0.25); border-radius:10px;
            font-size:12px; font-family:'DM Sans','Segoe UI',sans-serif; padding:0 16px; }
        QPushButton:hover { background:rgba(52,211,153,0.22); }
    """)
    qvb.addWidget(retry_btn, alignment=Qt.AlignCenter)

    vb.addWidget(quiz_card)

    BTN_DEFAULT  = "QPushButton{background:rgba(167,139,250,0.08);color:#a78bfa;border:1px solid rgba(167,139,250,0.20);border-radius:10px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:16px;}QPushButton:hover{background:rgba(167,139,250,0.18);}"
    BTN_CORRECT  = "QPushButton, QPushButton:disabled{background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.40);border-radius:10px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:16px;}"
    BTN_WRONG    = "QPushButton, QPushButton:disabled{background:rgba(255,77,109,0.12);color:#ff4d6d;border:1px solid rgba(255,77,109,0.35);border-radius:10px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:16px;}"
    BTN_DISABLED = "QPushButton, QPushButton:disabled{background:rgba(255,255,255,0.04);color:rgba(240,244,255,0.25);border:1px solid rgba(255,255,255,0.06);border-radius:10px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:16px;}"

    def _load(idx):
        if idx >= len(QUIZZES):
            pct = round(_state["score"] / len(QUIZZES) * 100)
            question_lbl.setText(f"🎉  Quiz terminé !  Score : {_state['score']} / {len(QUIZZES)}  ({pct}%)")
            for btn in choice_btns: btn.hide()
            expl_lbl.hide(); next_btn.hide(); q_counter.setText("Terminé")
            retry_btn.show()
            return
        q = QUIZZES[idx]
        q_counter.setText(f"Q {idx+1} / {len(QUIZZES)}")
        score_lbl.setText(f"Score : {_state['score']} / {idx}")
        question_lbl.setText(q["question"])
        expl_lbl.hide(); next_btn.hide(); retry_btn.hide()
        for i, (letter, txt, _) in enumerate(q["choices"]):
            btn = choice_btns[i]; btn.show()
            btn.setText(f"  {letter}.  {txt}")
            btn.setEnabled(True); btn.setStyleSheet(BTN_DEFAULT)

    def _answer(ci):
        idx = _state["current"]
        if _state["answered"][idx] is not None: return
        _state["answered"][idx] = ci
        _, _, correct = QUIZZES[idx]["choices"][ci]
        if correct: _state["score"] += 1
        for i, (_, _, is_correct) in enumerate(QUIZZES[idx]["choices"]):
            btn = choice_btns[i]; btn.setEnabled(False)
            if is_correct:         btn.setStyleSheet(BTN_CORRECT)
            elif i == ci:          btn.setStyleSheet(BTN_WRONG)
            else:                  btn.setStyleSheet(BTN_DISABLED)
        expl_lbl.setText(f"💡  {QUIZZES[idx]['explication']}"); expl_lbl.show()
        next_btn.show()
        score_lbl.setText(f"Score : {_state['score']} / {idx+1}")

    def _next():
        _state["current"] += 1; _load(_state["current"])

    def _retry():
        _state["current"] = 0
        _state["score"] = 0
        _state["answered"] = [None] * len(QUIZZES)
        _load(0)

    for i in range(4): choice_btns[i].clicked.connect(lambda _, ci=i: _answer(ci))
    next_btn.clicked.connect(_next)
    retry_btn.clicked.connect(_retry)
    _load(0)

    vb.addStretch()
    sv.setWidget(inner)
    out = QWidget(); out.setStyleSheet("background:transparent;")
    out_vb = QVBoxLayout(out); out_vb.setContentsMargins(0, 0, 0, 0); out_vb.addWidget(sv)
    return out


# ══════════════════════════════════════════════
#  PAGE : PROGRESSION
# ══════════════════════════════════════════════
def build_progression_page(etudiant_info: dict) -> QWidget:
    page = QWidget(); page.setStyleSheet("background:transparent;")
    sv = mk_scroll()

    inner = QWidget(); inner.setStyleSheet("background:transparent;")
    vb = QVBoxLayout(inner); vb.setContentsMargins(28, 24, 28, 24); vb.setSpacing(16)

    vb.addWidget(mk_label("Ma Progression", 20, "#f0f4ff", True,
                           "'Syne','Segoe UI Black',sans-serif"))
    vb.addWidget(mk_label("Votre parcours académique et votre activité sur NeuroDetect.",
                           12, "rgba(240,244,255,0.45)"))
    vb.addWidget(mk_divider())

    # ── profil académique depuis DB ──
    prof_card = mk_card()
    pv = QVBoxLayout(prof_card); pv.setContentsMargins(20, 16, 20, 16); pv.setSpacing(12)
    pv.addWidget(mk_label("🎓  Profil académique", 13, "#f0f4ff", True))
    pv.addWidget(mk_divider())

    profil_items = [
        ("Type d'établissement", etudiant_info.get("type_ecole",    "") or "—"),
        ("Établissement",        etudiant_info.get("etablissement", "") or "—"),
        ("Filière",              etudiant_info.get("filiere",       "") or "—"),
        ("Année d'études",       etudiant_info.get("annee_etude",   "") or "—"),
        ("CNE",                  etudiant_info.get("cne",           "") or "Non renseigné"),
        ("E-mail",               etudiant_info.get("email",         "") or "—"),
    ]

    grid = QGridLayout(); grid.setSpacing(10)
    for i, (k, v) in enumerate(profil_items):
        ri, ci = divmod(i, 2)
        cell = QFrame()
        cell.setStyleSheet("QFrame{background:rgba(255,255,255,0.04);border-radius:10px;border:none;}")
        cvb = QVBoxLayout(cell); cvb.setContentsMargins(12, 10, 12, 10); cvb.setSpacing(3)
        cvb.addWidget(mk_label(k, 10, "rgba(240,244,255,0.35)"))
        cvb.addWidget(mk_label(v, 12, "#f0f4ff", True))
        grid.addWidget(cell, ri, ci)
    pv.addLayout(grid)
    vb.addWidget(prof_card)

    # ── stats plateforme ──
    total_cas = get_total_analyses()
    stats_row = QHBoxLayout(); stats_row.setSpacing(12)
    for icon, val, lbl, col in [
        ("🔬", str(total_cas),          "Analyses dans la DB",  "#00d4ff"),
        ("📋", str(min(total_cas, 20)), "Cas consultables",     "#a78bfa"),
        ("🧩", "5",                     "Questions quiz",       "#34d399"),
        ("📅", etudiant_info.get("created_at", "—")[:10]
                if etudiant_info.get("created_at") else "—",
               "Membre depuis",          "#fbbf24"),
    ]:
        sc = mk_card(14); sc_vb = QVBoxLayout(sc)
        sc_vb.setContentsMargins(14, 12, 14, 12); sc_vb.setSpacing(4)
        ic = QLabel(icon); ic.setFixedSize(30, 30); ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"font-size:14px;background:rgba(0,0,0,0.2);border-radius:8px;border:1px solid {col}33;")
        sc_vb.addWidget(ic)
        sc_vb.addWidget(mk_label(val, 20, col, True, "'Syne','Segoe UI Black',sans-serif"))
        sc_vb.addWidget(mk_label(lbl, 10, "rgba(240,244,255,0.40)"))
        stats_row.addWidget(sc)
    vb.addLayout(stats_row)

    # ── activité sur la plateforme ──
    vb.addWidget(mk_label("Activité sur la plateforme", 15, "#f0f4ff", True,
                           "'Syne','Segoe UI Black',sans-serif"))

    if total_cas == 0:
        vb.addWidget(mk_empty_state(
            "📊",
            "Aucune activité enregistrée",
            "Les statistiques apparaîtront ici dès que\n"
            "des analyses IRM seront effectuées."
        ))
    else:
        act_card = mk_card()
        av = QVBoxLayout(act_card); av.setContentsMargins(18, 14, 18, 14); av.setSpacing(10)
        av.addWidget(mk_label(f"📈  {total_cas} analyse(s) IRM disponible(s) dans la base de données.",
                               13, "#f0f4ff"))
        av.addWidget(mk_label(
            "Consultez les cas cliniques pour explorer les résultats réels du modèle NeuroDetect.",
            12, "rgba(240,244,255,0.45)"
        ))
        vb.addWidget(act_card)

    vb.addStretch()
    sv.setWidget(inner)
    out = QWidget(); out.setStyleSheet("background:transparent;")
    out_vb = QVBoxLayout(out); out_vb.setContentsMargins(0, 0, 0, 0); out_vb.addWidget(sv)
    return out


# ══════════════════════════════════════════════
#  STUDENT DASHBOARD
# ══════════════════════════════════════════════
class StudentDashboardPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._user       = {}
        self._etudiant   = {}

        if main_window and hasattr(main_window, "current_user") and main_window.current_user:
            u = main_window.current_user
            self._user = u
            uid = u.get("id")
            if uid:
                self._etudiant = get_etudiant_info(uid)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background:#04080f;")
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        IMG_PATH = os.path.join(BASE_DIR, "assets", "medical.jpg")
        self.bg = QLabel(self)
        if os.path.exists(IMG_PATH):
            self.bg.setPixmap(QPixmap(IMG_PATH)); self.bg.setScaledContents(True)
        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background:rgba(4,8,15,0.88); border:none;")

        self.ui = QWidget(self); self.ui.setStyleSheet("background:transparent;")
        root = QHBoxLayout(self.ui)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), stretch=1)

        self.bg.lower(); self.overlay.raise_(); self.ui.raise_()

    # ── SIDEBAR ────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sb = QWidget(); sb.setFixedWidth(220)
        sb.setStyleSheet("""
            QWidget { background:rgba(6,12,24,0.95);
                border-right:1px solid rgba(255,255,255,0.06); }
        """)
        vb = QVBoxLayout(sb); vb.setContentsMargins(16, 28, 16, 20); vb.setSpacing(6)

        # brand
        icon_b = QLabel("🧠"); icon_b.setFixedSize(34, 34); icon_b.setAlignment(Qt.AlignCenter)
        icon_b.setStyleSheet("""
            font-size:16px;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #a78bfa,stop:1 #7c3aed);
            border-radius:9px; border:none;
        """)
        bname = mk_label("NeuroDetect", 14, "#f0f4ff", True,
                          "'Syne','Segoe UI Black',sans-serif")
        br = QHBoxLayout(); br.setSpacing(10)
        br.addWidget(icon_b); br.addWidget(bname); br.addStretch()
        vb.addLayout(br); vb.addSpacing(10)

        # profil étudiant
        fullname = self._user.get("fullname", "Étudiant")
        annee    = self._etudiant.get("annee_etude",   "") or ""
        etabl    = self._etudiant.get("etablissement", "") or ""
        etabl_s  = (etabl[:20] + "…") if len(etabl) > 20 else etabl
        sub_txt  = " · ".join(filter(None, [annee, etabl_s])) or "NeuroDetect"

        sc = QFrame()
        sc.setStyleSheet("""
            QFrame { background:rgba(167,139,250,0.06); border-radius:12px;
                border:1px solid rgba(167,139,250,0.15); }
        """)
        sv2 = QVBoxLayout(sc); sv2.setContentsMargins(12, 10, 12, 10); sv2.setSpacing(2)
        sv2.addWidget(mk_label(f"🎓  {fullname}", 12, "#f0f4ff", True))
        sv2.addWidget(mk_label(sub_txt, 10, "rgba(240,244,255,0.40)"))
        vb.addWidget(sc); vb.addSpacing(16)

        vb.addWidget(mk_label("NAVIGATION", 9, "rgba(240,244,255,0.25)"))
        vb.addSpacing(6)

        self._nav_btns = []
        for icon, label, idx in [
            ("📋", "Cas Cliniques", 0),
            ("🧩", "Quiz",          1),
            ("📈", "Progression",   2),
        ]:
            btn = NavBtn(icon, label, active=(idx == 0))
            btn.clicked.connect(lambda _, i=idx: self._switch(i))
            self._nav_btns.append(btn); vb.addWidget(btn)

        vb.addStretch(); vb.addWidget(mk_divider()); vb.addSpacing(8)

        logout = QPushButton("⎋  Déconnexion"); logout.setFixedHeight(42)
        logout.setCursor(Qt.PointingHandCursor)
        logout.setStyleSheet("""
            QPushButton { background:rgba(255,77,109,0.08); color:rgba(255,77,109,0.80);
                border:1px solid rgba(255,77,109,0.15); border-radius:12px; font-size:12px;
                font-family:'DM Sans','Segoe UI',sans-serif;
                text-align:left; padding-left:14px; }
            QPushButton:hover { background:rgba(255,77,109,0.15); color:#ff4d6d; }
        """)
        if self.main_window:
            logout.clicked.connect(self.main_window.go_login)
        vb.addWidget(logout)
        return sb

    # ── CONTENT ────────────────────────────────
    def _build_content(self) -> QWidget:
        w = QWidget(); w.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(w); vb.setContentsMargins(0, 0, 0, 0); vb.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        self._stack.addWidget(build_cas_cliniques())
        self._stack.addWidget(build_quiz_page())
        self._stack.addWidget(build_progression_page(self._etudiant))

        vb.addWidget(self._stack)
        return w

    def _switch(self, idx: int):
        # Rebuild pages dynamically with fresh data
        if idx == 0:
            old_w = self._stack.widget(0)
            new_w = build_cas_cliniques()
            self._stack.removeWidget(old_w)
            self._stack.insertWidget(0, new_w)
            old_w.deleteLater()
        elif idx == 2:
            old_w = self._stack.widget(2)
            new_w = build_progression_page(self._etudiant)
            self._stack.removeWidget(old_w)
            self._stack.insertWidget(2, new_w)
            old_w.deleteLater()

        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == idx)

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        for widget in (self.bg, self.overlay, self.ui):
            widget.setGeometry(0, 0, w, h)
        super().resizeEvent(event)