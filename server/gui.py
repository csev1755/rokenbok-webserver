import datetime
import logging
import os
import queue
import time

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QColor, QBrush
from PyQt6.QtWidgets import QGroupBox, QHeaderView, QLabel, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


class GUILogHandler(logging.Handler):
    """Custom logging handler that parses log records and pushes structured tuples into a thread-safe queue."""

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()

    def emit(self, record):
        try:
            time_str = datetime.datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            level = record.levelname
            name = record.name
            msg = record.getMessage()
            self.queue.put((time_str, level, name, msg))
        except Exception:
            self.handleError(record)


class MultiRokGUI(QMainWindow):
    LOG_COLORS = {
        "DEBUG": QColor("#888888"),
        "INFO": QColor("#FFFFFF"),
        "WARNING": QColor("#FFF000"),
        "ERROR": QColor("#FF5555"),
        "CRITICAL": QColor("#FF0000"),
    }

    def __init__(self, play_manager, go2rtc=None, bundle_dir="."):
        super().__init__()
        self.play_manager = play_manager
        self.go2rtc = go2rtc
        self.bundle_dir = bundle_dir

        self.setWindowTitle("MultiRok Server")
        self.resize(650, 550)
        self.setMinimumSize(480, 400)
        self.setup_icon()

        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Status Summary Group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        self.uptime_label = QLabel("Uptime: 00:00:00")
        status_layout.addWidget(self.uptime_label)
        main_layout.addWidget(status_group)

        # Connected Players List Group
        self.list_group = QGroupBox("Connected Players:")
        list_layout = QVBoxLayout(self.list_group)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Player ID", "Player Name", "Vehicle ID", "Vehicle Name"])
        self.tree.setFixedHeight(220)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(0)

        header = self.tree.header()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.tree.setColumnWidth(0, 65)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 65)

        list_layout.addWidget(self.tree)
        main_layout.addWidget(self.list_group)

        # Server Logs Group
        log_group = QGroupBox("Server Logs")
        log_layout = QVBoxLayout(log_group)

        self.log_tree = QTreeWidget()
        self.log_tree.setColumnCount(4)
        self.log_tree.setHeaderLabels(["Time", "Level", "Name", "Message"])
        self.log_tree.setRootIsDecorated(False)
        self.log_tree.setIndentation(0)

        log_header = self.log_tree.header()
        if log_header:
            log_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            log_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            log_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            log_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.log_tree.setColumnWidth(0, 65)
        self.log_tree.setColumnWidth(1, 70)
        self.log_tree.setColumnWidth(2, 100)

        log_layout.addWidget(self.log_tree)
        main_layout.addWidget(log_group, stretch=1)

        # Logging Handler Setup
        self.log_handler = GUILogHandler()

        # Track start time for uptime calculation
        self.start_time = time.time()

        # UI & Log Timers
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(500)

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.poll_logs)
        self.log_timer.start(100)

    def setup_icon(self):
        icon_path = os.path.join(self.bundle_dir, "server", "web", "favicon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def update_ui(self):
        elapsed_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}"
        self.uptime_label.setText(uptime_str)

        if not self.play_manager:
            return

        self.tree.clear()
        connected_count = 0

        for player_id, player in self.play_manager.players.items():
            if player.socket_id:
                connected_count += 1
                name = player.player_name or "No Name"

                selection_id_text = "None"
                vehicle_name_text = "None"

                if player.selection:
                    selection_id_text = str(player.selection)
                    vehicle = self.play_manager.get_vehicle_from_id(player.selection)
                    if vehicle:
                        vehicle_name_text = vehicle.name

                self.tree.addTopLevelItem(QTreeWidgetItem([str(player_id), name, selection_id_text, vehicle_name_text]))

        self.list_group.setTitle(f"Connected Players: {connected_count} / {self.play_manager.max_player_count}")

    def poll_logs(self):
        new_logs = []
        while True:
            try:
                new_logs.append(self.log_handler.queue.get_nowait())
            except queue.Empty:
                break

        if not new_logs:
            return

        colored_new_logs = []
        for log_entry in new_logs:
            item = QTreeWidgetItem(log_entry)
            item.setForeground(0, QBrush(QColor("#888888")))
            color = self.LOG_COLORS.get(log_entry[1], QColor("#FFFFFF"))
            brush = QBrush(color)
            for col in (1, 2, 3):
                item.setForeground(col, brush)
            colored_new_logs.append(item)

        self.log_tree.addTopLevelItems(colored_new_logs)

        while self.log_tree.topLevelItemCount() > 256:
            self.log_tree.takeTopLevelItem(0)

        self.log_tree.scrollToBottom()

    def closeEvent(self, event):
        if self.go2rtc:
            self.go2rtc.stop()
        event.accept()
