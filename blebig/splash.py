from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from .paths import resource_path


class Splash(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 520)
        self.setStyleSheet("""
            QWidget#card { background:#080b16; border:1px solid #25345f; border-radius:28px; }
            QLabel { color:white; font-family:'Segoe UI'; }
            QProgressBar { border:0; background:#161c33; border-radius:4px; max-height:8px; }
            QProgressBar::chunk { border-radius:4px; background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2788ff,stop:1 #7858ff); }
        """)
        card = QWidget(self); card.setObjectName("card"); card.setGeometry(20, 20, 420, 480)
        layout = QVBoxLayout(card); layout.setContentsMargins(55, 45, 55, 38); layout.setSpacing(16)
        icon = QLabel(); icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(QPixmap(str(resource_path("assets/blebig.png"))).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title = QLabel("BLEBIG"); title.setAlignment(Qt.AlignmentFlag.AlignCenter); title.setStyleSheet("font-size:29px;font-weight:800;letter-spacing:4px")
        tagline = QLabel("MỞ RỘNG KHÔNG GIỚI HẠN"); tagline.setAlignment(Qt.AlignmentFlag.AlignCenter); tagline.setStyleSheet("color:#aab6d8;font-size:12px;letter-spacing:2px")
        self.bar = QProgressBar(); self.bar.setRange(0, 0); self.bar.setTextVisible(False)
        layout.addWidget(icon); layout.addWidget(title); layout.addWidget(tagline); layout.addStretch(); layout.addWidget(self.bar)
        self.setWindowOpacity(0)
        self.fade_in = QPropertyAnimation(self, b"windowOpacity"); self.fade_in.setDuration(550); self.fade_in.setStartValue(0); self.fade_in.setEndValue(1); self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event); self.fade_in.start()

    def finish_into(self, window):
        self._window = window
        QTimer.singleShot(900, self._finish)

    def _finish(self):
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(350); animation.setStartValue(1); animation.setEndValue(0)
        animation.finished.connect(self._show_window); self._fade_out = animation; animation.start()

    def _show_window(self):
        self.hide(); self._window.show(); self._window.raise_(); self._window.activateWindow()

