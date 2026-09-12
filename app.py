from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QThread, QTimer, Qt, Signal, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QListWidget, QMainWindow,
    QMessageBox, QProgressBar, QProgressDialog, QPushButton, QSpinBox, QVBoxLayout, QWidget,
    QInputDialog)

from .diagnostics import run_diagnostics
from .engine import ExpandOptions, expand, fit_for_content
from .layout import PRESETS_CM, calculate_layout, engine_anchor_for_area
from .logging_setup import configure_logging
from .paths import log_dir, resource_path, update_dir
from .settings import load_custom_sizes, save_custom_sizes

LOG = logging.getLogger("blebig.app")
FILTER = "Ảnh (*.png *.jpg *.jpeg *.webp *.tif *.tiff)"
STYLE = """
QMainWindow,QWidget{background:#090b15;color:#f5f7ff;font-family:'Segoe UI';font-size:13px}
QLabel{background:transparent}
QFrame#panel{background:#101425;border:1px solid #242b49;border-radius:18px}
QLabel#title{font-size:25px;font-weight:700} QLabel#muted{color:#9ca8c7}
QLabel#preview{background:#070912;border:1px dashed #34406b;border-radius:18px;color:#8d98b7}
QPushButton{background:#171d34;border:1px solid #30395e;border-radius:10px;padding:9px 13px}
QPushButton:hover{background:#202947;border-color:#4386ff}
QPushButton#primary{font-weight:700;padding:13px;border:0;background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1877ff,stop:.55 #275cff,stop:1 #7655ff)}
QComboBox,QSpinBox,QDoubleSpinBox{background:#0b0f1d;border:1px solid #2c3558;border-radius:8px;padding:6px;min-height:24px}
QListWidget{background:#0b0f1d;border:1px solid #2c3558;border-radius:10px}
QProgressBar{background:#0b0f1d;border:1px solid #2c3558;border-radius:7px;text-align:center}
QProgressBar::chunk{border-radius:6px;background:#3478ff} QMenuBar{background:#090b15} QMenu{background:#12172a}
"""


class BatchWorker(QThread):
    progress = Signal(int, int, str)
    preview = Signal(object)
    completed = Signal(list)
    failed = Signal(str)

    def __init__(self, paths, output_dir, layout, mode, anchor, dpi):
        super().__init__(); self.paths = paths; self.output_dir = output_dir
        self.layout = layout; self.mode = mode; self.anchor = anchor; self.dpi = dpi

    def run(self):
        outputs = []
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for index, path in enumerate(self.paths, 1):
                self.progress.emit(index - 1, len(self.paths), f"Đang xử lý {path.name}")
                with Image.open(path) as opened: source = opened.convert("RGB")
                fitted = fit_for_content(source, self.layout.content_width_px, self.layout.content_height_px)
                result = expand(fitted, ExpandOptions(self.layout.output_width_px,
                    self.layout.output_height_px, self.anchor, self.mode),
                    lambda msg: self.progress.emit(index - 1, len(self.paths), msg))
                output = self._unique_output(path)
                result.save(output, dpi=(self.dpi, self.dpi), quality=96)
                outputs.append(output)
                if index == 1: self.preview.emit(result)
                self.progress.emit(index, len(self.paths), f"Hoàn thành {path.name}")
            self.completed.emit(outputs)
        except Exception:
            LOG.exception("Xử lý hàng loạt thất bại"); self.failed.emit(traceback.format_exc())

    def _unique_output(self, source):
        suffix = source.suffix.lower() if source.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"} else ".png"
        candidate = self.output_dir / f"{source.stem}_BleBig{suffix}"; counter = 2
        while candidate.exists():
            candidate = self.output_dir / f"{source.stem}_BleBig_{counter}{suffix}"; counter += 1
        return candidate


class OnlineCheckWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def run(self):
        try:
            from .online_update import check_latest
            self.completed.emit(check_latest())
        except Exception as exc:
            LOG.warning("Không kiểm tra được GitHub Update: %s", exc)
            self.failed.emit(str(exc))


class OnlineDownloadWorker(QThread):
    progress = Signal(object, object)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, release):
        super().__init__(); self.release = release

    def run(self):
        try:
            from .online_update import download_release
            self.completed.emit(download_release(self.release, self.progress.emit))
        except Exception:
            LOG.exception("Tải bản cập nhật thất bại")
            self.failed.emit(traceback.format_exc())


class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.paths = []; self.preview_image = None; self.worker = None; self.output_dir = None
        self.custom_sizes = load_custom_sizes(); self._applying_preset = False; self._restoring = False
        self._history = []; self._history_index = -1; self._processing = False; self.update_check_worker = None; self.update_download_worker = None; self.update_progress = None
        self.setWindowTitle("BleBig — Tràn nền thông minh"); self.setWindowIcon(QIcon(str(resource_path("assets/blebig.png"))))
        self.resize(1220, 800); self.setStyleSheet(STYLE); self._build_ui(); self._push_history(); self._diagnose(); self._show_update_result()
        QTimer.singleShot(1800, self._start_online_update_check)

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central); root.setContentsMargins(18,18,18,18); root.setSpacing(16)
        panel = QFrame(); panel.setObjectName("panel"); panel.setFixedWidth(390)
        controls = QVBoxLayout(panel); controls.setContentsMargins(18,18,18,18); controls.setSpacing(9); root.addWidget(panel)
        head = QHBoxLayout(); logo = QLabel(); logo.setPixmap(QPixmap(str(resource_path("assets/blebig.png"))).scaled(58,58,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        titles = QVBoxLayout(); title = QLabel("BleBig"); title.setObjectName("title"); subtitle = QLabel("Tràn nền thông minh cho in ấn"); subtitle.setObjectName("muted")
        titles.addWidget(title); titles.addWidget(subtitle); head.addWidget(logo); head.addLayout(titles); head.addStretch(); controls.addLayout(head)
        open_btn = QPushButton("＋  Mở ảnh / Chọn nhiều ảnh"); open_btn.clicked.connect(self.open_images); controls.addWidget(open_btn)
        self.files = QListWidget(); self.files.setMaximumHeight(105); controls.addWidget(self.files)
        history_row = QHBoxLayout(); self.undo_btn = QPushButton("↶  UNDO"); self.redo_btn = QPushButton("↷  REDO")
        self.undo_btn.clicked.connect(self.undo); self.redo_btn.clicked.connect(self.redo); history_row.addWidget(self.undo_btn); history_row.addWidget(self.redo_btn); controls.addLayout(history_row)

        size_title = QLabel("KÍCH THƯỚC"); size_title.setStyleSheet("color:#7da8ff;font-size:11px;font-weight:700;letter-spacing:1px;margin-top:4px"); controls.addWidget(size_title)
        form = QFormLayout(); form.setSpacing(7)
        self.preset = QComboBox(); self.preset.addItems([*PRESETS_CM.keys(), *self.custom_sizes.keys(), "Tùy chọn", "＋ Thêm kích thước…"]); self.preset.setCurrentText("A4 dọc"); self.preset.currentTextChanged.connect(self._preset_changed)
        self.width_cm = QDoubleSpinBox(); self.width_cm.setRange(.1,500); self.width_cm.setDecimals(2); self.width_cm.setSuffix(" cm")
        self.height_cm = QDoubleSpinBox(); self.height_cm.setRange(.1,500); self.height_cm.setDecimals(2); self.height_cm.setSuffix(" cm")
        self.bleed_cm = QDoubleSpinBox(); self.bleed_cm.setRange(0,20); self.bleed_cm.setDecimals(2); self.bleed_cm.setSingleStep(.1); self.bleed_cm.setValue(.3); self.bleed_cm.setSuffix(" cm")
        self.placement = QComboBox(); self.placement.addItems(["Tràn từ kích thước đã chọn", "Tràn trong kích thước đã chọn"]); self.placement.setCurrentIndex(1)
        self.anchor = QComboBox(); self.anchor.addItems(["Giữa","Trái","Phải","Trên","Dưới"])
        self.mode = QComboBox(); self.mode.addItems(["Nhanh — Offline","AI LaMa — CPU"])
        self.dpi = QSpinBox(); self.dpi.setRange(72,1200); self.dpi.setValue(300); self.dpi.setSuffix(" DPI")
        self.width_cm.valueChanged.connect(self._dimension_changed); self.height_cm.valueChanged.connect(self._dimension_changed)
        self.bleed_cm.valueChanged.connect(self._state_changed); self.placement.currentTextChanged.connect(self._state_changed); self.dpi.valueChanged.connect(self._state_changed); self.anchor.currentTextChanged.connect(self._state_changed); self.mode.currentTextChanged.connect(self._state_changed)
        form.addRow("Kích thước",self.preset); form.addRow("Ngang",self.width_cm); form.addRow("Dọc",self.height_cm); controls.addLayout(form)
        bleed_title = QLabel("QUY CÁCH TRÀN"); bleed_title.setStyleSheet("color:#7da8ff;font-size:11px;font-weight:700;letter-spacing:1px;margin-top:4px"); controls.addWidget(bleed_title)
        bleed_form = QFormLayout(); bleed_form.setSpacing(7); bleed_form.addRow("Khoảng cách",self.bleed_cm); bleed_form.addRow("Chế độ",self.placement); bleed_form.addRow("Khu vực",self.anchor); bleed_form.addRow("Xử lý",self.mode); bleed_form.addRow("Độ phân giải",self.dpi); controls.addLayout(bleed_form)
        self.summary = QLabel(); self.summary.setWordWrap(True); self.summary.setObjectName("muted"); controls.addWidget(self.summary)
        out_btn = QPushButton("Chọn thư mục lưu"); out_btn.clicked.connect(self.choose_output); controls.addWidget(out_btn)
        self.output_label = QLabel("Mặc định: BleBig_Output cạnh ảnh gốc"); self.output_label.setObjectName("muted"); self.output_label.setWordWrap(True); controls.addWidget(self.output_label)
        run_btn = QPushButton("TRÀN NỀN"); run_btn.setObjectName("primary"); run_btn.clicked.connect(self.process); controls.addWidget(run_btn)
        self.progress = QProgressBar(); self.progress.setValue(0); controls.addWidget(self.progress)
        self.status = QLabel("Sẵn sàng"); self.status.setObjectName("muted"); controls.addWidget(self.status)
        bottom = QHBoxLayout(); log_btn = QPushButton("Log"); log_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(log_dir())))); update_btn = QPushButton("Thư mục Update"); update_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(update_dir())))); bottom.addWidget(log_btn); bottom.addWidget(update_btn); controls.addLayout(bottom)
        self.preview = QLabel("Kéo một hoặc nhiều ảnh vào đây"); self.preview.setObjectName("preview"); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumSize(700,690); root.addWidget(self.preview,1)
        self._preset_changed("A4 dọc"); self._update_history_buttons()
        menu = self.menuBar().addMenu("Trợ giúp"); diag = QAction("Chạy chẩn đoán",self); diag.triggered.connect(self._diagnose); menu.addAction(diag); self.setAcceptDrops(True)

    def _preset_changed(self, name):
        if name == "＋ Thêm kích thước…":
            label, ok = QInputDialog.getText(self, "Thêm kích thước", "Tên kích thước:")
            if ok and label.strip():
                clean = label.strip(); self.custom_sizes[clean] = (self.width_cm.value(), self.height_cm.value()); save_custom_sizes(self.custom_sizes)
                self.preset.insertItem(self.preset.count()-2, clean); self.preset.setCurrentText(clean)
            else: self.preset.setCurrentText("Tùy chọn")
            return
        custom = name == "Tùy chọn"; self.width_cm.setEnabled(True); self.height_cm.setEnabled(True)
        sizes = {**PRESETS_CM, **self.custom_sizes}
        if name in sizes:
            self._applying_preset = True; w,h = sizes[name]; self.width_cm.setValue(w); self.height_cm.setValue(h); self._applying_preset = False
        self._state_changed()

    def _layout(self):
        areas={"Giữa":"center","Trái":"left","Phải":"right","Trên":"top","Dưới":"bottom"}
        return calculate_layout(self.width_cm.value(),self.height_cm.value(),self.bleed_cm.value(),self.dpi.value(),"outside" if self.placement.currentIndex()==0 else "inside",areas[self.anchor.currentText()])

    def _refresh_summary(self,*_):
        try:
            layout = self._layout()
            if self.placement.currentIndex()==0: text=f"Đầu ra: {layout.output_width_cm:.2f} × {layout.output_height_cm:.2f} cm · {layout.output_width_px} × {layout.output_height_px} px"
            else: text=f"Đầu ra: {layout.output_width_cm:.2f} × {layout.output_height_cm:.2f} cm · vùng ảnh {layout.content_width_cm:.2f} × {layout.content_height_cm:.2f} cm"
            self.summary.setText(text)
        except ValueError as exc: self.summary.setText(str(exc))

    def _dimension_changed(self, *_):
        if self._applying_preset:
            self._refresh_summary(); return
        if not self._applying_preset and self.preset.currentText() != "Tùy chọn":
            self.preset.blockSignals(True); self.preset.setCurrentText("Tùy chọn"); self.preset.blockSignals(False)
        self._state_changed()

    def _snapshot(self):
        return tuple(self.paths)

    def _state_changed(self, *_):
        self._refresh_summary()

    def _push_history(self):
        state = self._snapshot()
        if not state: return
        if self._history_index >= 0 and self._history[self._history_index] == state: return
        self._history = self._history[:self._history_index + 1]; self._history.append(state)
        if len(self._history) > 80: self._history.pop(0)
        self._history_index = len(self._history) - 1; self._update_history_buttons()

    def _restore_state(self, state):
        self.paths = list(state)
        self.files.clear(); self.files.addItems([p.name for p in self.paths])
        with Image.open(self.paths[0]) as image: self._show_image(image.convert("RGB"))
        self.status.setText("Đã khôi phục ảnh — có thể chỉnh thông số và tràn tiếp")
        self._update_history_buttons()

    def undo(self):
        if self._processing: return
        if self._history_index > 0:
            self._history_index -= 1; self._restore_state(self._history[self._history_index])

    def redo(self):
        if self._processing: return
        if self._history_index + 1 < len(self._history):
            self._history_index += 1; self._restore_state(self._history[self._history_index])

    def _update_history_buttons(self):
        if not hasattr(self, "undo_btn"): return
        self.undo_btn.setEnabled(not self._processing and self._history_index > 0)
        self.redo_btn.setEnabled(not self._processing and self._history_index + 1 < len(self._history))

    def open_images(self):
        paths,_=QFileDialog.getOpenFileNames(self,"Chọn ảnh","",FILTER)
        if paths:self.load_paths(paths)

    def load_paths(self,paths):
        if self._processing:
            QMessageBox.information(self,"BleBig","Hãy chờ xử lý xong trước khi chọn ảnh mới."); return
        accepted=[]
        for raw in paths:
            path=Path(raw)
            try:
                with Image.open(path) as image:image.verify()
                accepted.append(path)
            except Exception:LOG.warning("Bỏ qua file không phải ảnh: %s",path)
        if not accepted:return
        self.paths=accepted;self.files.clear();self.files.addItems([p.name for p in accepted])
        self.default_output_dir = accepted[0].parent / "BleBig_Output"
        with Image.open(accepted[0]) as image:self.preview_image=image.convert("RGB")
        self._show_image(self.preview_image);self.status.setText(f"Đã chọn {len(accepted)} ảnh")
        self._history = []; self._history_index = -1; self._push_history()

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dropEvent(self,event):self.load_paths([u.toLocalFile() for u in event.mimeData().urls()])
    def choose_output(self):
        path=QFileDialog.getExistingDirectory(self,"Chọn thư mục lưu")
        if path:self.output_dir=Path(path);self.output_label.setText(path)

    def process(self):
        if self._processing: return
        if not self.paths:QMessageBox.information(self,"BleBig","Hãy chọn ít nhất một ảnh.");return
        try:layout=self._layout()
        except ValueError as exc:QMessageBox.warning(self,"BleBig",str(exc));return
        output=self.output_dir or self.default_output_dir;mode="ai" if self.mode.currentIndex() else "fast"
        self._processing = True; self._update_history_buttons()
        self.worker=BatchWorker(list(self.paths),output,layout,mode,engine_anchor_for_area(layout.area),self.dpi.value());self.worker.progress.connect(self._progress);self.worker.completed.connect(self._completed);self.worker.failed.connect(self._failed);self.progress.setRange(0,len(self.paths));self.worker.start()
    def _progress(self,value,total,message):self.progress.setRange(0,total);self.progress.setValue(value);self.status.setText(message)
    def _completed(self,outputs):
        self._processing = False
        self._restore_state(outputs); self._push_history()
        self.progress.setValue(len(outputs));self.status.setText(f"Hoàn tất {len(outputs)} ảnh — UNDO để hoàn tác kết quả");QMessageBox.information(self,"BleBig",f"Đã xử lý {len(outputs)} ảnh.\nLưu tại:\n{outputs[0].parent}")
    def _failed(self,detail):
        self._processing = False; self._update_history_buttons()
        self.status.setText("Xử lý thất bại — ảnh trước đó vẫn được giữ");QMessageBox.critical(self,"BleBig",detail[-1000:])
    def _show_image(self,image):
        self.preview_image=image;pix=QPixmap.fromImage(ImageQt(image.convert("RGBA"))).scaled(self.preview.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation);self.preview.setPixmap(pix)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.preview_image:self._show_image(self.preview_image)
    def _diagnose(self):
        report=run_diagnostics();LOG.info("Chẩn đoán:\n%s","\n".join(report.lines))
    def _show_update_result(self):
        from .update_manager import consume_update_result
        message=consume_update_result()
        if message:QMessageBox.information(self,"BleBig Update",message)

    def _start_online_update_check(self):
        if self.update_check_worker and self.update_check_worker.isRunning(): return
        self.update_check_worker = OnlineCheckWorker(self)
        self.update_check_worker.completed.connect(self._offer_online_update)
        self.update_check_worker.start()

    def _offer_online_update(self, release):
        if not release: return
        box = QMessageBox(self); box.setWindowTitle("BleBig Update")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(f"Đã có BleBig {release.version}")
        box.setInformativeText(f"{release.changes[:1800]}\n\nBạn muốn cập nhật ngay không?")
        update_button = box.addButton("Cập nhật ngay", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Để sau", QMessageBox.ButtonRole.RejectRole); box.exec()
        if box.clickedButton() is update_button: self._download_online_update(release)

    def _download_online_update(self, release):
        self.update_progress = QProgressDialog("Đang tải bản cập nhật…", "Ẩn", 0, 100, self)
        self.update_progress.setWindowTitle("BleBig Update"); self.update_progress.setAutoClose(False); self.update_progress.setValue(0)
        self.update_download_worker = OnlineDownloadWorker(release)
        self.update_download_worker.progress.connect(self._online_download_progress)
        self.update_download_worker.completed.connect(self._online_download_completed)
        self.update_download_worker.failed.connect(self._online_download_failed)
        self.update_download_worker.start()

    def _online_download_progress(self, received, total):
        if total > 0: self.update_progress.setValue(min(99, int(received * 100 / total)))
        else: self.update_progress.setRange(0, 0)

    def _online_download_completed(self, package):
        self.update_progress.close()
        from .update_manager import launch_package
        if launch_package(Path(package)):
            QApplication.quit()
        else:
            QMessageBox.critical(self, "BleBig Update", "Không thể mở trình cập nhật. Gói đã được giữ trong thư mục Update.")

    def _online_download_failed(self, detail):
        self.update_progress.close()
        QMessageBox.warning(self, "BleBig Update", "Không tải được bản cập nhật. Bạn vẫn có thể tiếp tục sử dụng BleBig.\n\n" + detail[-500:])


def main():
    configure_logging();LOG.info("Khởi động BleBig")
    app=QApplication(sys.argv);app.setApplicationName("BleBig");app.setOrganizationName("Thien Ha");app.setWindowIcon(QIcon(str(resource_path("assets/blebig.png"))))
    from .splash import Splash
    splash=Splash();splash.show();app.processEvents()
    from .update_manager import offer_pending_update
    if offer_pending_update():return 0
    window=Window();splash.finish_into(window);return app.exec()
