import datetime
import logging
import os
import queue
import time

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QColor, QBrush
from PyQt6.QtWidgets import QGroupBox, QHeaderView, QLabel, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


class GUILogHandler(logging.Handler):
    """
    Custom logging handler that parses and queues log records.
    """

    def __init__(self):
        super().__init__()
        self.log_queue = queue.Queue()

    def emit(self, record):
        try:
            time_str = datetime.datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            level = record.levelname
            name = record.name
            msg = record.getMessage()
            self.log_queue.put((time_str, level, name, msg))
        except Exception:
            self.handleError(record)


class MultiRokGUI(QMainWindow):
    """
    PyQt main window for control of MultiRok server.

    Attributes:
        play_manager (PlayManager): MultiRok server's PlayManager object.
        go2rtc (Go2RTC): MultiRok server's Go2RTC process.
        bundle_dir (str): Program root directory for serving favicon.
    """

    LOG_COLORS = {
        "DEBUG": QColor("#888888"),
        "INFO": QColor("#FFFFFF"),
        "WARNING": QColor("#FFF000"),
        "ERROR": QColor("#FF5555"),
        "CRITICAL": QColor("#FF0000"),
    }

    def __init__(self, play_manager, go2rtc=None, bundle_dir="."):
        """
        Initializes the main window.
        """

        super().__init__()
        self.play_manager = play_manager
        self.go2rtc = go2rtc
        self.bundle_dir = bundle_dir

        self.setWindowTitle("MultiRok Server")
        self.resize(650, 550)
        self.setMinimumSize(650, 550)

        # Set Main Window Icon
        icon_path = os.path.join(self.bundle_dir, "server", "web", "favicon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Status Group Box
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        self.uptime_label = QLabel("Uptime: 00:00:00")
        status_layout.addWidget(self.uptime_label)
        main_layout.addWidget(status_group)

        # Connected Players Group
        self.player_list_group = QGroupBox("Connected Players: 0 / 0")
        player_list_layout = QVBoxLayout(self.player_list_group)

        self.player_list_tree = QTreeWidget()
        self.player_list_tree.setColumnCount(4)
        self.player_list_tree.setHeaderLabels(["Player ID", "Player Name", "Vehicle ID", "Vehicle Name"])
        self.player_list_tree.setFixedHeight(220)
        self.player_list_tree.setRootIsDecorated(False)
        self.player_list_tree.setIndentation(0)

        player_list_tree_header = self.player_list_tree.header()
        if player_list_tree_header:
            player_list_tree_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            player_list_tree_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            player_list_tree_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            player_list_tree_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.player_list_tree.setColumnWidth(0, 65)
        self.player_list_tree.setColumnWidth(1, 150)
        self.player_list_tree.setColumnWidth(2, 65)

        player_list_layout.addWidget(self.player_list_tree)
        main_layout.addWidget(self.player_list_group)

        # Server Logs Group
        log_group = QGroupBox("Server Logs")
        log_layout = QVBoxLayout(log_group)

        self.log_tree = QTreeWidget()
        self.log_tree.setColumnCount(4)
        self.log_tree.setHeaderLabels(["Time", "Level", "Name", "Message"])
        self.log_tree.setRootIsDecorated(False)
        self.log_tree.setIndentation(0)

        log_tree_header = self.log_tree.header()
        if log_tree_header:
            log_tree_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            log_tree_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            log_tree_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            log_tree_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.log_tree.setColumnWidth(0, 65)
        self.log_tree.setColumnWidth(1, 70)
        self.log_tree.setColumnWidth(2, 100)

        log_layout.addWidget(self.log_tree)
        main_layout.addWidget(log_group, stretch=1)

        # Logging Handler Setup
        self.log_handler = GUILogHandler()

        # Track start time for uptime calculation
        self.start_time = time.time()

        # GUI & Log Refresh Timers for Polling
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_gui)
        self.ui_timer.start(500)

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_logs)
        self.log_timer.start(100)

    def update_gui(self):
        """
        Polls the necessary information from the play_manager to update the GUI.
        """

        # Uptime Counter
        elapsed_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")

        if not self.play_manager:
            return

        # Player List
        self.player_list_tree.clear()
        connected_player_count = 0

        for player_id, player in self.play_manager.players.items():
            if player.socket_id:
                connected_player_count += 1
                name = player.player_name or "No Name"

                selection_id_text = "None"
                vehicle_name_text = "None"

                if player.selection:
                    selection_id_text = str(player.selection)
                    vehicle = self.play_manager.get_vehicle_from_id(player.selection)
                    if vehicle:
                        vehicle_name_text = vehicle.name

                self.player_list_tree.addTopLevelItem(QTreeWidgetItem([str(player_id), name, selection_id_text, vehicle_name_text]))

        # Total Player Count
        self.player_list_group.setTitle(f"Connected Players: {connected_player_count} / {self.play_manager.max_player_count}")

    def update_logs(self):
        """
        Polls the custom log handler queue to update the log display on the GUI.
        """
        new_logs = []
        while True:
            try:
                new_logs.append(self.log_handler.log_queue.get_nowait())
            except queue.Empty:
                break

        if not new_logs:
            return

        # Color Logs According to Severity
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

        # Limit Total Number of Log Entries
        while self.log_tree.topLevelItemCount() > 256:
            self.log_tree.takeTopLevelItem(0)

        self.log_tree.scrollToBottom()

    def closeEvent(self, event):
        """
        Handle closing the main window.
        """
        if self.go2rtc:
            self.go2rtc.stop()
        event.accept()
