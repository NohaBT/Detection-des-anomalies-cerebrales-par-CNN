"""
doctor_dashboard.py  —  Dashboard Médecin connecté au vrai modèle IA
"""
import os
import sys
import math
import random

# ── path fix ──
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFrame,
    QVBoxLayout, QHBoxLayout, QScrollArea,
    QGraphicsDropShadowEffect, QFileDialog,
    QProgressBar, QSizePolicy, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QStackedWidget
)
from PySide6.QtGui import (
    QPixmap, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QFont
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal

from database import save_analyse, get_analyses_by_medecin
from predictor import predict, warmup


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
    f.setStyleSheet(f"""
        QFrame {{
            background:rgba(8,16,32,0.85);
            border-radius:{radius}px;
            border:1px solid rgba(255,255,255,0.07);
        }}
    """)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(30); shadow.setOffset(0, 8)
    shadow.setColor(QColor(0, 0, 0, 80))
    f.setGraphicsEffect(shadow)
    return f


# ══════════════════════════════════════════════
#  AI WORKER THREAD  (predict sans bloquer l'UI)
# ══════════════════════════════════════════════
class PredictWorker(QThread):
    finished = Signal(dict)

    def __init__(self, image_path: str):
        super().__init__()
        self._path = image_path

    def run(self):
        result = predict(self._path)
        self.finished.emit(result)


# ══════════════════════════════════════════════
#  STAT CARD
# ══════════════════════════════════════════════
class StatCard(QFrame):
    def __init__(self, icon, value, label, accent="#00d4ff", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame { background:rgba(8,16,32,0.85); border-radius:16px;
                border:1px solid rgba(255,255,255,0.07); }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24); shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        vb = QVBoxLayout(self)
        vb.setContentsMargins(20, 18, 20, 18); vb.setSpacing(6)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(38, 38); icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size:18px;background:rgba(0,212,255,0.10);border:1px solid {accent}33;border-radius:10px;")

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color:{accent};font-size:28px;font-weight:800;font-family:'Syne','Segoe UI Black',sans-serif;background:transparent;border:none;")

        lab_lbl = mk_label(label, size=11, color="rgba(240,244,255,0.45)")

        vb.addWidget(icon_lbl); vb.addSpacing(4)
        vb.addWidget(val_lbl); vb.addWidget(lab_lbl)


# ══════════════════════════════════════════════
#  MINI BAR CHART
# ══════════════════════════════════════════════
class MiniBarChart(QWidget):
    def __init__(self, data, labels, accent="#00d4ff", parent=None):
        super().__init__(parent)
        self._data = data; self._labels = labels
        self._accent = QColor(accent)
        self.setMinimumHeight(120)
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, e):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            if not self._data or w <= 0 or h <= 0:
                return
            mx = max(self._data) if max(self._data) > 0 else 1   # fix ZeroDivisionError
            n = len(self._data)
            if n == 0:
                return
            bar_w   = max(12, (w - 20) // n - 8)
            spacing = (w - 20 - bar_w * n) // max(n - 1, 1)
            for i, val in enumerate(self._data):
                bh = max(2, int((val / mx) * (h - 30)))
                x  = 10 + i * (bar_w + spacing)
                y  = h - 22 - bh
                grad = QLinearGradient(x, y, x, y + bh)
                grad.setColorAt(0, QColor(self._accent))
                grad.setColorAt(1, QColor(0, 102, 255))
                p.setBrush(QBrush(grad)); p.setPen(Qt.NoPen)
                p.drawRoundedRect(x, y, bar_w, bh, 4, 4)
                p.setPen(QPen(QColor(240, 244, 255, 100)))
                p.setFont(QFont("Segoe UI", 8))
                p.drawText(x, h - 6, self._labels[i] if i < len(self._labels) else "")
        finally:
            p.end()  # toujours fermer le painter


# ══════════════════════════════════════════════
#  NAV BUTTON
# ══════════════════════════════════════════════
class NavBtn(QPushButton):
    def __init__(self, icon, label, active=False, parent=None):
        super().__init__(parent)
        self._active = active
        self.setText(f"  {icon}  {label}")
        self.setFixedHeight(46); self.setCursor(Qt.PointingHandCursor)
        self._apply()

    def set_active(self, val):
        self._active = val; self._apply()

    def _apply(self):
        if self._active:
            self.setStyleSheet("QPushButton{background:rgba(0,212,255,0.12);color:#00d4ff;border:none;border-radius:12px;font-size:13px;font-weight:600;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:14px;}")
        else:
            self.setStyleSheet("QPushButton{background:transparent;color:rgba(240,244,255,0.55);border:none;border-radius:12px;font-size:13px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:14px;}QPushButton:hover{background:rgba(255,255,255,0.05);color:rgba(240,244,255,0.85);}")


# ══════════════════════════════════════════════
#  UPLOAD ZONE
# ══════════════════════════════════════════════
class UploadZone(QFrame):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)
        self._filepath = None
        self._apply_style(False)

        vb = QVBoxLayout(self); vb.setAlignment(Qt.AlignCenter); vb.setSpacing(8)

        self.icon_lbl = QLabel("🧠")
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("font-size:32px;background:transparent;border:none;")

        self.main_lbl = mk_label("Glisser une image IRM ici", size=14, color="#f0f4ff", bold=True)
        self.main_lbl.setAlignment(Qt.AlignCenter)

        self.sub_lbl = mk_label("ou cliquer pour parcourir  ·  PNG, JPG, JPEG",
                                 size=11, color="rgba(240,244,255,0.40)")
        self.sub_lbl.setAlignment(Qt.AlignCenter)

        self.browse_btn = QPushButton("Parcourir les fichiers")
        self.browse_btn.setFixedHeight(36); self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setStyleSheet("QPushButton{background:rgba(0,212,255,0.12);color:#00d4ff;border:1px solid rgba(0,212,255,0.30);border-radius:9px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;padding:0 20px;}QPushButton:hover{background:rgba(0,212,255,0.20);}")
        self.browse_btn.clicked.connect(self._browse)

        vb.addWidget(self.icon_lbl); vb.addWidget(self.main_lbl)
        vb.addWidget(self.sub_lbl); vb.addSpacing(6)
        vb.addWidget(self.browse_btn, alignment=Qt.AlignCenter)

    def _apply_style(self, hovered):
        border = "rgba(0,212,255,0.50)" if hovered else "rgba(0,212,255,0.20)"
        bg     = "rgba(0,212,255,0.07)" if hovered else "rgba(0,212,255,0.03)"
        self.setStyleSheet(f"QFrame{{background:{bg};border:2px dashed {border};border-radius:16px;}}")

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner une IRM", "",
                                               "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self._set_file(path)

    def _set_file(self, path):
        self._filepath = path
        self.file_selected.emit(path)
        name = os.path.basename(path)
        self.icon_lbl.setText("✅")
        self.main_lbl.setText(name)
        self.sub_lbl.setText("Fichier prêt pour l'analyse IA")
        self._apply_style(False)

    def reset(self):
        self._filepath = None
        self.icon_lbl.setText("🧠")
        self.main_lbl.setText("Glisser une image IRM ici")
        self.sub_lbl.setText("ou cliquer pour parcourir  ·  PNG, JPG, JPEG")
        self._apply_style(False)

    def get_path(self): return self._filepath

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction(); self._apply_style(True)
    def dragLeaveEvent(self, e): self._apply_style(False)
    def dropEvent(self, event):
            if event.mimeData().hasUrls():
                event.setDropAction(Qt.CopyAction)
                event.accept()
                
                url = event.mimeData().urls()[0]
                
                local_path = url.toLocalFile()
                
                self.selected_image_path = local_path
                print(f"[DEBUG] Image reçue par Drag & Drop : {self.selected_image_path}")

                # ... الكود القديم ديال الـ dropEvent ...
                self.selected_image_path = local_path
                print(f"[DEBUG] Image reçue par Drag & Drop : {self.selected_image_path}")
                
                # 🛠️ التعديل المصحح: كنعرضو الصورة نيشان ف الـ Label ديال الـ Preview
                # (تأكدي غي من سمية الـ label ديال الصورة عندك، غالباً غيكون سميتو حاجة بحال label_image أو preview_label)
                if hasattr(self, 'label_image'):
                    pixmap = QPixmap(local_path)
                    # تصغير الصورة بش تجي قد المربع للي حاطة ف الـ UI
                    scaled_pixmap = pixmap.scaled(self.label_image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.label_image.setPixmap(scaled_pixmap)
                else:
                    # إلا كانت سميتو ف الكود هي preview_label مثلاً:
                    if hasattr(self, 'preview_label'):
                        pixmap = QPixmap(local_path)
                        scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.preview_label.setPixmap(scaled_pixmap)
                    
                # لتحديث الواجهة وإخفاء نصوص الـ Drag القديمة
                if hasattr(self, 'label_info'):
                    self.label_info.setText("Fichier prêt pour l'analyse IA")
                
            else:
                event.ignore()


# ══════════════════════════════════════════════
#  RESULT PANEL
# ══════════════════════════════════════════════
class ResultPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame{background:rgba(8,16,32,0.85);border-radius:16px;border:1px solid rgba(255,255,255,0.07);}")
        self._vb = QVBoxLayout(self)
        self._vb.setContentsMargins(20, 20, 20, 20); self._vb.setSpacing(12)
        self._show_placeholder()

    def _clear(self):
        while self._vb.count():
            item = self._vb.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _show_placeholder(self):
        self._clear()
        ph = mk_label("⬆  Uploadez une IRM pour lancer l'analyse IA",
                       size=13, color="rgba(240,244,255,0.25)")
        ph.setAlignment(Qt.AlignCenter)
        self._vb.addStretch(); self._vb.addWidget(ph, alignment=Qt.AlignCenter); self._vb.addStretch()

    def show_loading(self):
        self._clear()
        self._vb.addStretch()
        spinner = mk_label("🔄  Analyse IA en cours...", size=14, color="#00d4ff", bold=True)
        spinner.setAlignment(Qt.AlignCenter)
        prog = QProgressBar(); prog.setRange(0, 0); prog.setFixedHeight(6)
        prog.setStyleSheet("QProgressBar{background:rgba(255,255,255,0.08);border-radius:3px;border:none;}QProgressBar::chunk{background:#00d4ff;border-radius:3px;}")
        sub = mk_label("MobileNetV2 · Classification IRM", size=11, color="rgba(240,244,255,0.30)")
        sub.setAlignment(Qt.AlignCenter)
        self._vb.addWidget(spinner, alignment=Qt.AlignCenter)
        self._vb.addSpacing(12); self._vb.addWidget(prog)
        self._vb.addSpacing(8); self._vb.addWidget(sub, alignment=Qt.AlignCenter)
        self._vb.addStretch()

    def show_error(self, msg: str):
        self._clear()
        self._vb.addStretch()
        err = mk_label(f"⚠  {msg}", size=12, color="#ff4d6d")
        err.setAlignment(Qt.AlignCenter)
        self._vb.addWidget(err, alignment=Qt.AlignCenter)
        self._vb.addStretch()

    def show_result(self, result: dict):
        self._clear()
        color = result["color"]

        # ── titre ──
        title_row = QHBoxLayout()
        dot = QLabel(); dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background:{color};border-radius:5px;border:none;")
        title = mk_label(
            result["label"] + (" — Détecté" if result["detected"] else " — Aucune tumeur"),
            size=15, bold=True, color=color
        )
        title_row.addWidget(dot, alignment=Qt.AlignVCenter)
        title_row.addSpacing(8); title_row.addWidget(title); title_row.addStretch()
        self._vb.addLayout(title_row)
        self._vb.addWidget(mk_divider())

        # ── confiance ──
        conf_row = QHBoxLayout()
        conf_row.addWidget(mk_label(f"Confiance IA :", size=12, color="rgba(240,244,255,0.60)"))
        conf_row.addStretch()
        conf_row.addWidget(mk_label(f"{result['confidence']}%", size=13, color=color, bold=True))
        self._vb.addLayout(conf_row)
        bar = QProgressBar(); bar.setValue(result["confidence"]); bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"QProgressBar{{background:rgba(255,255,255,0.08);border-radius:4px;border:none;}}QProgressBar::chunk{{background:{color};border-radius:4px;}}")
        self._vb.addWidget(bar)

        # ── détails grid ──
        grid = QGridLayout(); grid.setSpacing(10)
        details = [
            ("Type",         result.get("type",        "—")),
            ("Localisation", result.get("localisation","—")),
            ("Grade",        result.get("grade",       "—")),
            ("Gravité",      result.get("gravite",     "—")),
        ]
        for i, (k, v) in enumerate(details):
            row_i, col_i = divmod(i, 2)
            cell = QFrame()
            cell.setStyleSheet("QFrame{background:rgba(255,255,255,0.04);border-radius:10px;border:none;}")
            cvb = QVBoxLayout(cell); cvb.setContentsMargins(12, 10, 12, 10); cvb.setSpacing(3)
            cvb.addWidget(mk_label(k, size=10, color="rgba(240,244,255,0.35)"))
            cvb.addWidget(mk_label(v, size=13, color="#f0f4ff", bold=True))
            grid.addWidget(cell, row_i, col_i)
        self._vb.addLayout(grid)

        # ── probabilités toutes les classes ──
        if result.get("all_probs"):
            self._vb.addWidget(mk_label("Distribution des probabilités", size=11,
                                         color="rgba(240,244,255,0.40)"))
            CLASS_COLORS = {
                "glioma":     "#ff4d6d",
                "meningioma": "#fbbf24",
                "pituitary":  "#a78bfa",
                "notumor":    "#34d399",
            }
            CLASS_LABELS = {
                "glioma":     "Gliome",
                "meningioma": "Méningiome",
                "pituitary":  "Tumeur hypoph.",
                "notumor":    "Pas de tumeur",
            }
            for cls, prob in sorted(result["all_probs"].items(),
                                    key=lambda x: x[1], reverse=True):
                col_cls = CLASS_COLORS.get(cls, "#00d4ff")
                tr = QHBoxLayout(); tr.setSpacing(10)
                name_lbl = mk_label(CLASS_LABELS.get(cls, cls), size=11,
                                     color="rgba(240,244,255,0.65)")
                name_lbl.setFixedWidth(120)
                pbar = QProgressBar(); pbar.setValue(int(prob)); pbar.setFixedHeight(6)
                pbar.setTextVisible(False)
                pbar.setStyleSheet(f"QProgressBar{{background:rgba(255,255,255,0.07);border-radius:3px;border:none;}}QProgressBar::chunk{{background:{col_cls};border-radius:3px;}}")
                prob_lbl = mk_label(f"{prob:.1f}%", size=11, color=col_cls, bold=True)
                prob_lbl.setFixedWidth(50)
                tr.addWidget(name_lbl); tr.addWidget(pbar); tr.addWidget(prob_lbl)
                self._vb.addLayout(tr)

        # ── recommandation ──
        rec = QFrame()
        rec.setStyleSheet(f"QFrame{{background:rgba(0,212,255,0.06);border-radius:10px;border:1px solid rgba(0,212,255,0.15);}}")
        rvb = QVBoxLayout(rec); rvb.setContentsMargins(14, 10, 14, 10); rvb.setSpacing(4)
        rvb.addWidget(mk_label("💡 Recommandation clinique", size=11, color="#00d4ff"))
        rvb.addWidget(mk_label(result.get("recommendation", "—"),
                                size=12, color="rgba(240,244,255,0.70)"))
        self._vb.addWidget(rec)


# ══════════════════════════════════════════════
#  PAGE : ANALYSE IRM
# ══════════════════════════════════════════════
def build_analyse_page(medecin_id=None) -> QWidget:
    page = QWidget(); page.setStyleSheet("background:transparent;")
    vb   = QVBoxLayout(page); vb.setContentsMargins(28, 24, 28, 24); vb.setSpacing(16)

    title = mk_label("Analyse IRM", size=20, bold=True,
                      family="'Syne','Segoe UI Black',sans-serif")
    sub   = mk_label("Uploadez une IRM — le modèle MobileNetV2 classifie en temps réel.",
                      size=12, color="rgba(240,244,255,0.45)")
    vb.addWidget(title); vb.addWidget(sub); vb.addWidget(mk_divider())

    row = QHBoxLayout(); row.setSpacing(16)

    # left col
    left_col = QVBoxLayout(); left_col.setSpacing(12)
    upload   = UploadZone()

    analyse_btn = QPushButton("🔬  Lancer l'analyse IA")
    analyse_btn.setFixedHeight(48); analyse_btn.setCursor(Qt.PointingHandCursor)
    analyse_btn.setEnabled(False)
    analyse_btn.setStyleSheet("""
        QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00d4ff,stop:1 #0066ff);
            color:white;border:none;border-radius:12px;font-size:14px;font-weight:700;
            font-family:'Syne','Segoe UI Black',sans-serif;letter-spacing:0.08em;}
        QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33ddff,stop:1 #2288ff);}
        QPushButton:disabled{background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.3);}
    """)

    reset_btn = QPushButton("↺  Nouvelle analyse")
    reset_btn.setFixedHeight(38); reset_btn.setCursor(Qt.PointingHandCursor)
    reset_btn.setVisible(False)
    reset_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.05);color:rgba(240,244,255,0.55);border:1px solid rgba(255,255,255,0.09);border-radius:10px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;}QPushButton:hover{background:rgba(255,255,255,0.10);color:#f0f4ff;}")

    left_col.addWidget(upload)
    left_col.addWidget(analyse_btn)
    left_col.addWidget(reset_btn)
    left_col.addStretch()

    # right: result panel
    result_panel = ResultPanel()
    result_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    _worker = [None]

    # enable btn when file selected
    def _on_file(path):
        analyse_btn.setEnabled(True)
        reset_btn.setVisible(False)

    upload.file_selected.connect(_on_file)

    def _on_analyse():
        path = upload.get_path()
        if not path:
            return
        analyse_btn.setEnabled(False)
        result_panel.show_loading()

        worker = PredictWorker(path)
        _worker[0] = worker

        def _on_done(result):
            analyse_btn.setEnabled(True)
            reset_btn.setVisible(True)
            if not result["success"]:
                result_panel.show_error(result["error"])
                return
            result_panel.show_result(result)
            # sauvegarder dans la DB
            if medecin_id:
                try:
                    save_analyse(medecin_id, {
                        "resultat":     result["label"],
                        "type_tumeur":  result["type"],
                        "localisation": result["localisation"],
                        "grade":        result["grade"],
                        "confiance":    result["confidence"] / 100.0,
                        "image_path":   path,
                    })
                except Exception:
                    pass

        worker.finished.connect(_on_done)
        worker.start()

    def _on_reset():
        upload.reset()
        result_panel._show_placeholder()
        analyse_btn.setEnabled(False)
        reset_btn.setVisible(False)

    analyse_btn.clicked.connect(_on_analyse)
    reset_btn.clicked.connect(_on_reset)

    row.addLayout(left_col, stretch=2)
    row.addWidget(result_panel, stretch=3)
    vb.addLayout(row, stretch=1)
    return page


# ══════════════════════════════════════════════
#  PAGE : HISTORIQUE
# ══════════════════════════════════════════════
def build_historique_page(medecin_id=None) -> QWidget:
    page = QWidget(); page.setStyleSheet("background:transparent;")
    vb   = QVBoxLayout(page); vb.setContentsMargins(28, 24, 28, 24); vb.setSpacing(16)

    title = mk_label("Historique des analyses", size=20, bold=True,
                      family="'Syne','Segoe UI Black',sans-serif")
    sub   = mk_label("Toutes les analyses IRM effectuées sur la plateforme.",
                      size=12, color="rgba(240,244,255,0.45)")
    vb.addWidget(title); vb.addWidget(sub); vb.addWidget(mk_divider())

    table = QTableWidget()
    table.setColumnCount(6)
    table.setHorizontalHeaderLabels(["Date", "Patient", "Type tumeur",
                                      "Localisation", "Résultat", "Confiance"])
    table.setStyleSheet("""
        QTableWidget{background:rgba(8,16,32,0.85);color:#f0f4ff;
            border:1px solid rgba(255,255,255,0.07);border-radius:14px;
            gridline-color:rgba(255,255,255,0.05);font-size:12px;
            font-family:'DM Sans','Segoe UI',sans-serif;outline:none;}
        QHeaderView::section{background:rgba(0,212,255,0.08);color:#00d4ff;
            border:none;border-bottom:1px solid rgba(0,212,255,0.15);
            padding:10px 12px;font-size:11px;font-weight:600;letter-spacing:0.06em;}
        QTableWidget::item{padding:10px 12px;border:none;}
        QTableWidget::item:selected{background:rgba(0,212,255,0.12);color:#f0f4ff;}
        QScrollBar:vertical{background:transparent;width:4px;}
        QScrollBar::handle:vertical{background:rgba(0,212,255,0.25);border-radius:2px;}
        QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
    """)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setEditTriggers(QTableWidget.NoEditTriggers)

    # charger depuis la DB
    rows = []
    if medecin_id:
        try:
            rows = get_analyses_by_medecin(medecin_id)
        except Exception:
            pass

    if rows:
        table.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            date_str = str(row_data.get("date_analyse", "—"))[:16]
            patient  = row_data.get("patient_nom",  "—")
            typ      = row_data.get("type_tumeur",  "—")
            loc      = row_data.get("localisation", "—")
            res      = row_data.get("resultat",     "—")
            conf     = row_data.get("confiance",    0)
            conf_str = f"{round(conf * 100)}%" if conf else "—"

            for c, val in enumerate([date_str, patient, typ, loc, res, conf_str]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if c == 4:
                    is_detected = res not in ("—", "Aucune tumeur", "notumor")
                    item.setForeground(QColor("#ff4d6d" if is_detected else "#34d399"))
                table.setItem(r, c, item)
            table.setRowHeight(r, 46)
    else:
        table.setRowCount(1)
        item = QTableWidgetItem("Aucune analyse enregistrée pour le moment.")
        item.setForeground(QColor("rgba(240,244,255,0.35)"))
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(0, 0, item)
        table.setSpan(0, 0, 1, 6)
        table.setRowHeight(0, 80)

    vb.addWidget(table, stretch=1)
    return page


# ══════════════════════════════════════════════
#  PAGE : STATS
# ══════════════════════════════════════════════
def build_stats_page(medecin_id=None) -> QWidget:
    page = QWidget(); page.setStyleSheet("background:transparent;")
    sv = QScrollArea(); sv.setWidgetResizable(True); sv.setFrameShape(QFrame.NoFrame)
    sv.setStyleSheet("background:transparent;border:none;")
    sv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    inner = QWidget(); inner.setStyleSheet("background:transparent;")
    vb = QVBoxLayout(inner); vb.setContentsMargins(28, 24, 28, 24); vb.setSpacing(20)

    title = mk_label("Statistiques", size=20, bold=True,
                      family="'Syne','Segoe UI Black',sans-serif")
    sub   = mk_label("Aperçu global de votre activité diagnostique.",
                      size=12, color="rgba(240,244,255,0.45)")
    vb.addWidget(title); vb.addWidget(sub); vb.addWidget(mk_divider())

    # récupérer stats réelles depuis la DB
    total = 0; detected = 0; neg = 0
    type_counts = {"glioma": 0, "meningioma": 0, "pituitary": 0, "notumor": 0}
    avg_conf = 0.0
    monthly  = [0] * 6

    if medecin_id:
        try:
            rows = get_analyses_by_medecin(medecin_id)
            total = len(rows)
            confs = []
            for row_data in rows:
                res = str(row_data.get("resultat", "")).lower()
                if row_data.get("confiance"): confs.append(row_data["confiance"])
                # détecter si tumeur
                if res in ("gliome", "méningiome", "tumeur hypophysaire",
                           "glioma", "meningioma", "pituitary"):
                    detected += 1
                else:
                    neg += 1
                # type
                typ = str(row_data.get("type_tumeur", "")).lower()
                for k in type_counts:
                    if k in typ:
                        type_counts[k] += 1
                        break
            avg_conf = round(sum(confs) / len(confs) * 100) if confs else 0
        except Exception:
            pass

    # stat cards
    stats_row = QHBoxLayout(); stats_row.setSpacing(12)
    for icon, val, lbl, acc in [
        ("🧠", str(total),        "IRM analysées",      "#00d4ff"),
        ("⚠️",  str(detected),    "Tumeurs détectées",  "#ff4d6d"),
        ("✅",  str(neg),          "Résultats négatifs", "#34d399"),
        ("📈",  f"{avg_conf}%",   "Confiance moyenne",  "#a78bfa"),
    ]:
        stats_row.addWidget(StatCard(icon, val, lbl, acc))
    vb.addLayout(stats_row)

    # charts row
    charts_row = QHBoxLayout(); charts_row.setSpacing(12)

    # chart 1 — placeholder mensuel
    c1 = mk_card(); c1_vb = QVBoxLayout(c1)
    c1_vb.setContentsMargins(18, 16, 18, 16); c1_vb.setSpacing(10)
    c1_vb.addWidget(mk_label("Analyses par mois", size=13, bold=True))
    c1_vb.addWidget(mk_label("6 derniers mois", size=10, color="rgba(240,244,255,0.35)"))
    chart1 = MiniBarChart(monthly if any(monthly) else [0, 0, 0, 0, 0, total],
                          ["Jan","Fév","Mar","Avr","Mai","Jui"], "#00d4ff")
    chart1.setMinimumHeight(140)
    c1_vb.addWidget(chart1)
    charts_row.addWidget(c1, stretch=1)

    # chart 2 — types réels
    c2 = mk_card(); c2_vb = QVBoxLayout(c2)
    c2_vb.setContentsMargins(18, 16, 18, 16); c2_vb.setSpacing(10)
    c2_vb.addWidget(mk_label("Types de tumeurs détectées", size=13, bold=True))
    c2_vb.addWidget(mk_label("Distribution", size=10, color="rgba(240,244,255,0.35)"))
    tumor_data = [
        ("Gliome",         type_counts["glioma"],     "#ff4d6d"),
        ("Méningiome",     type_counts["meningioma"], "#a78bfa"),
        ("Tumeur hypoph.", type_counts["pituitary"],  "#fbbf24"),
        ("Pas de tumeur",  type_counts["notumor"],    "#34d399"),
    ]
    total_types = sum(type_counts.values()) or 1
    for name, cnt, col in tumor_data:
        pct = round(cnt / total_types * 100)
        tr = QHBoxLayout(); tr.setSpacing(10)
        dot = QLabel(); dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background:{col};border-radius:4px;border:none;")
        tr.addWidget(dot, alignment=Qt.AlignVCenter)
        tr.addWidget(mk_label(name, size=12, color="rgba(240,244,255,0.75)"))
        tr.addStretch()
        tr.addWidget(mk_label(f"{cnt} ({pct}%)", size=12, color=col, bold=True))
        bar2 = QProgressBar(); bar2.setValue(pct); bar2.setFixedHeight(5)
        bar2.setTextVisible(False)
        bar2.setStyleSheet(f"QProgressBar{{background:rgba(255,255,255,0.06);border-radius:3px;border:none;}}QProgressBar::chunk{{background:{col};border-radius:3px;}}")
        c2_vb.addLayout(tr); c2_vb.addWidget(bar2)
    charts_row.addWidget(c2, stretch=1)
    vb.addLayout(charts_row)
    vb.addStretch()

    sv.setWidget(inner)
    outer = QVBoxLayout(page); outer.setContentsMargins(0, 0, 0, 0); outer.addWidget(sv)
    return page


# ══════════════════════════════════════════════
#  DOCTOR DASHBOARD
# ══════════════════════════════════════════════
class DoctorDashboardPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._medecin_id = None
        if main_window and hasattr(main_window, "current_user") and main_window.current_user:
            self._medecin_id = main_window.current_user.get("id")
        self._build_ui()
        # warm-up modèle en arrière-plan
        QTimer.singleShot(500, warmup)

    def _build_ui(self):
        self.setStyleSheet("background:#04080f;")
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        IMG_PATH = os.path.join(BASE_DIR, "assets", "medical.jpg")
        self.bg = QLabel(self)
        if os.path.exists(IMG_PATH):
            self.bg.setPixmap(QPixmap(IMG_PATH)); self.bg.setScaledContents(True)
        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background:rgba(4,8,15,0.88);border:none;")

        self.ui = QWidget(self); self.ui.setStyleSheet("background:transparent;")
        root = QHBoxLayout(self.ui); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), stretch=1)

        self.bg.lower(); self.overlay.raise_(); self.ui.raise_()

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget(); sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("QWidget{background:rgba(6,12,24,0.95);border-right:1px solid rgba(255,255,255,0.06);}")
        vb = QVBoxLayout(sidebar); vb.setContentsMargins(16, 28, 16, 20); vb.setSpacing(6)

        brand = QHBoxLayout(); brand.setSpacing(10)
        icon_b = QLabel("🧠"); icon_b.setFixedSize(34, 34); icon_b.setAlignment(Qt.AlignCenter)
        icon_b.setStyleSheet("font-size:16px;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00d4ff,stop:1 #0066ff);border-radius:9px;border:none;")
        bname = mk_label("NeuroDetect", 14, "#f0f4ff", True, "'Syne','Segoe UI Black',sans-serif")
        brand.addWidget(icon_b); brand.addWidget(bname); brand.addStretch()
        vb.addLayout(brand); vb.addSpacing(8)

        # doctor info depuis current_user
        doc_name = "Médecin"
        doc_spec  = "NeuroDetect"
        if self.main_window and hasattr(self.main_window, "current_user") and self.main_window.current_user:
            u = self.main_window.current_user
            doc_name = u.get("fullname", "Médecin")
            doc_spec  = u.get("specialite", "Neurologie")

        doc_card = QFrame()
        doc_card.setStyleSheet("QFrame{background:rgba(0,212,255,0.06);border-radius:12px;border:1px solid rgba(0,212,255,0.12);}")
        dc_vb = QVBoxLayout(doc_card); dc_vb.setContentsMargins(12, 10, 12, 10); dc_vb.setSpacing(2)
        dc_vb.addWidget(mk_label(f"⚕️  {doc_name}", 12, "#f0f4ff", True))
        dc_vb.addWidget(mk_label(f"{doc_spec} · En ligne", 10, "rgba(240,244,255,0.40)"))
        vb.addWidget(doc_card); vb.addSpacing(16)

        vb.addWidget(mk_label("NAVIGATION", 9, "rgba(240,244,255,0.25)"))
        vb.addSpacing(6)

        self._nav_btns = []
        for icon, label, idx in [("🔬","Analyse IRM",0),("📋","Historique",1),("📊","Statistiques",2)]:
            btn = NavBtn(icon, label, active=(idx == 0))
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            self._nav_btns.append(btn); vb.addWidget(btn)

        vb.addStretch(); vb.addWidget(mk_divider()); vb.addSpacing(8)

        logout_btn = QPushButton("⎋  Déconnexion")
        logout_btn.setFixedHeight(42); logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet("QPushButton{background:rgba(255,77,109,0.08);color:rgba(255,77,109,0.80);border:1px solid rgba(255,77,109,0.15);border-radius:12px;font-size:12px;font-family:'DM Sans','Segoe UI',sans-serif;text-align:left;padding-left:14px;}QPushButton:hover{background:rgba(255,77,109,0.15);color:#ff4d6d;}")
        if self.main_window:
            logout_btn.clicked.connect(self.main_window.go_login)
        vb.addWidget(logout_btn)
        return sidebar

    def _build_content(self) -> QWidget:
        content = QWidget(); content.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(content); vb.setContentsMargins(0, 0, 0, 0); vb.setSpacing(0)
        self._stack = QStackedWidget(); self._stack.setStyleSheet("background:transparent;")
        self._stack.addWidget(build_analyse_page(self._medecin_id))
        self._stack.addWidget(build_historique_page(self._medecin_id))
        self._stack.addWidget(build_stats_page(self._medecin_id))
        vb.addWidget(self._stack)
        return content

    def _switch_page(self, idx):
        # rebuild historique/stats pages with fresh data each time they're opened
        if idx == 1:
            old_w = self._stack.widget(1)
            new_w = build_historique_page(self._medecin_id)
            self._stack.removeWidget(old_w)
            self._stack.insertWidget(1, new_w)
            old_w.deleteLater()
        elif idx == 2:
            old_w = self._stack.widget(2)
            new_w = build_stats_page(self._medecin_id)
            self._stack.removeWidget(old_w)
            self._stack.insertWidget(2, new_w)
            old_w.deleteLater()

        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == idx)

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        self.bg.setGeometry(0, 0, w, h)
        self.overlay.setGeometry(0, 0, w, h)
        self.ui.setGeometry(0, 0, w, h)
        super().resizeEvent(event)