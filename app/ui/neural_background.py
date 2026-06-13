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
#  NEURAL CANVAS  (same as RegisterPage)
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

