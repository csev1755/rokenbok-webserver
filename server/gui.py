import datetime
import logging
import os
import queue

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
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
        self.players_label = QLabel("Connected Players: 0 / 0")
        status_layout.addWidget(self.players_label)
        main_layout.addWidget(status_group)

        # Connected Players List Group
        list_group = QGroupBox("Connected Players List")
        list_layout = QVBoxLayout(list_group)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["ID", "Player Name", "Selection ID", "Vehicle Name"])
        self.tree.setFixedHeight(220)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(0)

        header = self.tree.header()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.tree.setColumnWidth(0, 45)
        self.tree.setColumnWidth(1, 130)
        self.tree.setColumnWidth(2, 90)

        list_layout.addWidget(self.tree)
        main_layout.addWidget(list_group)

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

        self.log_tree.setColumnWidth(0, 85)
        self.log_tree.setColumnWidth(1, 75)
        self.log_tree.setColumnWidth(2, 110)

        log_layout.addWidget(self.log_tree)
        main_layout.addWidget(log_group, stretch=1)

        # Logging Handler Setup
        self.log_handler = GUILogHandler()

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

        self.players_label.setText(f"Connected Players: {connected_count} / {self.play_manager.max_player_count}")

    def poll_logs(self):
        while not self.log_handler.queue.empty():
            try:
                time_str, level, name, msg = self.log_handler.queue.get_nowait()
                item = QTreeWidgetItem([time_str, level, name, msg])

                self.log_tree.addTopLevelItem(item)
                self.log_tree.scrollToItem(item)
            except queue.Empty:
                break

    def closeEvent(self, event):
        if self.go2rtc:
            self.go2rtc.stop()
        event.accept()
        os._exit(0)
