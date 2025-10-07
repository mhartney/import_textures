# === Project Configuration ===

import os, sys

def set_up_project():
    """Confgure env for running application."""
    file_path = "/dept/ra/mhartney/MariTools/texture_import_tool_edit/apps/frontend/import_textures.py"
    sys.modules["__main__"].__file__ = file_path
    file_parent = os.path.dirname(__file__)
    parent_dir = os.path.dirname(file_parent)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)

def close_previous_app():
    """Close previous instance of application."""
    try:
        __window.close()
        __window.deleteLater()
    except Exception as e:
        print(f"[DEBUG] {e}")
        pass

set_up_project()
close_previous_app()

# === Imports ===
import time
import subprocess
import json
import os
import re

from pathlib import Path
from PySide2 import QtWidgets
from PySide2.QtCore import Qt, QTimer, Slot, QPointF, QSizeF
from PySide2.QtGui import QBrush, QColor
from datetime import datetime

import backend
import mariCommon as mc
import mari

# === Constant / Global Variables === 
# Example match / groups 'opacity.1001.tif' --> (opacity<name>)(.<sep>)(1001<udim>).(tif<ext>)
TXT_REGEX = re.compile(r'^(?P<name>.+?)(?P<sep>[^0-9])(?P<udim>\d{4})\.(?P<ext>\w+)$', re.IGNORECASE)
SCRIPT = "/dept/ra/mhartney/MariTools/texture_import_tool_edit/apps/backend/run_search.py"

# === Widgets ===

class Button(QtWidgets.QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(80, 30)
        self.setStyleSheet("color: white;")


    def disable_button(self):
        """Disable button when pressed."""
        QTimer.singleShot(0, lambda: (
            self.setEnabled(False),
            self.setStyleSheet("""
                        color: gray;
                        background-color; #f0f0f0;
            """)))
    

    def enable_button(self):
        """Enable button when task has finished."""
        QTimer.singleShot(0, lambda: (
            self.setEnabled(True),
            self.setStyleSheet("color: white;")))


class ToolButton(QtWidgets.QToolButton):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.hide()


class TableWidget(QtWidgets.QTableWidget):
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setMinimumHeight(27)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStyleSheet("""color: #dbdbdb; 
                                               font-weight: bold;""")
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setColumnCount(8)
        self.hide()


    def add_checkboxes(self, data):
        for row_index, _ in enumerate(data):
            checkbox_a = QtWidgets.QTableWidgetItem()
            checkbox_a.setFlags(Qt.ItemIsSelectable)
            checkbox_a.setForeground(QBrush(QColor("#dbdbdb")))
            checkbox_a.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_a.setText("")
            checkbox_a.setCheckState(Qt.CheckState.Unchecked)
            self.setItem(row_index, 0, checkbox_a)
            
            checkbox_b = QtWidgets.QCheckBox()
            checkbox_b.setStyleSheet("margin-left:50%; mrgin-right:50%;")
            self.setCellWidget(row_index, 7, checkbox_b)
    

    def populate_table(self, data):
        if not data:
            return

        headers = list(data[0].keys())
        self.setRowCount(len(data))
        self.setHorizontalHeaderLabels([""] + headers + ["Broadcaster"])
        self.add_checkboxes(data)
        
        combo_col = self.return_combo_dict()
        for row_index, row_dict in enumerate(data):
            for col_index, key in enumerate(headers):
                if key in combo_col:
                    combo = QtWidgets.QComboBox()
                    combo.setStyleSheet("color: #dbdbdb;")
                    combo.addItems(combo_col[key])
                    image_value = str(row_dict.get(key, ""))
                    combo.setCurrentText(image_value)
                    self.setCellWidget(row_index, col_index + 1, combo)
                else:
                    value = row_dict.get(key, "")
                    item = QtWidgets.QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemIsSelectable)
                    item.setForeground(QBrush(QColor("#dbdbdb")))
                    self.setItem(row_index, col_index + 1, item)
    

    def return_combo_dict(self):
        """Returns options for selection box."""
        return {"Depth": ["8-bit", "16-bit", "32-bit"],
                "Colourspace": ["color", "scalar"]}
    
# === Main Window ===

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Tool")
        self.setMinimumSize(600, 100)

        #  Widget configuration
        self.path_input_box = QtWidgets.QLineEdit()
        path = backend.path.default_path()
        self.path_input_box.setText(path)
        
        self.search_btn = Button()
        self.search_btn.setText("Scan")
        self.browse_btn = Button()
        self.browse_btn.setText("Browse")
        self.import_btn = Button()
        self.import_btn.setText("Import")


        self.select_all_btn = ToolButton()
        self.select_all_btn.setText("Select All")
        self.broadcaster_btn = ToolButton()
        self.broadcaster_btn.setText("Connect all Broadcasters")
        self.broadcaster_btn.setFixedSize(150, 20)

        self.table_widget = TableWidget()

        self.status_label = QtWidgets.QLabel()
        self.status_label.setStyleSheet("color: gray; " \
                                    "font-style: italic;")

        # Layout configuration
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(self.path_input_box)
        top_layout.addWidget(self.search_btn)
        top_layout.addWidget(self.browse_btn)

        second_row = QtWidgets.QHBoxLayout()
        second_row.addWidget(self.select_all_btn, alignment=Qt.AlignLeft)
        second_row.addWidget(self.broadcaster_btn, alignment=Qt.AlignRight)

        mid_layout = QtWidgets.QVBoxLayout()
        mid_layout.addWidget(self.table_widget)

        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addWidget(self.import_btn)
    
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(top_layout, stretch=1)
        main_layout.addSpacing(10)
        main_layout.addLayout(second_row, strecth=1)
        main_layout.addLayout(mid_layout, stretch=3)
        main_layout.addLayout(bottom_layout, stretch=1)
        main_layout.addStretch()
        self.setLayout(main_layout)

        # Slot connections
        if not hasattr(self, "_connected"):
            self.path_input_box.returnPressed.connect(self.search_btn_clicked)
            self.browse_btn.clicked.connect(self.browse_btn_clicked)
            self.search_btn.clicked.connect(self.search_btn_clicked)
            self.select_all_btn.clicked.connect(self.select_all_checkboxes)
            self.import_btn.clicked.connect(self.import_btn_selected)
            self.broadcaster_btn.clicked.connect(self.select_all_broadcaster)
            self._connected = True

        if not hasattr(self, "_data_source"):
            self._data_source = None

# === Widget Methods ===

    def update_status(self, message):
        """Updates label with input message, also refreshes
        GUI, and adds sleep for readability."""
        label = getattr(self, "status_label")
        if message:
            QTimer.singleShot(0, lambda: (label.setText(str(message)),
                                        label.repaint() 
                                        ))
            QtWidgets.QApplication.processEvents()
    

    def hide_table(self):
        QTimer.singleShot(0, lambda: (
            (self.table_widget.hide()),
            (self.select_all_btn.hide()),
            (self.broadcaster_btn.hide()),
            (self.status_label.setText(""))))
        QtWidgets.QApplication.processEvents()


    def show_table(self):
        QTimer.singleShot(0, lambda: (
            (self.table_widget.show()),
            (self.select_all_btn.show()),
            (self.broadcaster_btn.show())))
        QtWidgets.QApplication.processEvents()

    
    def adjust_table_size(self):
        for col in range(1, 6):
            self.table_widget.setColumnWidth(col, 100)
        self.table_widget.resizeRowsToContents()

        max_height = 0
        for row in range(self.table_widget.rowCount()):
            max_height += self.table_widget.rowHeight(row)
        
        max_width = 0
        for col in range(0, 8):
            max_width += self.table_widget.columnWidth(col)

        self.table_widget.setColumnWidth(0, 24)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)

        self.setMinimumSize(max_width -20, max_height)
        self.setMaximumSize(max_width + 100, max_height + 130)
        self.table_widget.setMaximumHeight(max_height + 130)
        self.table_widget.setMaximumWidth(max_width + 100)

# === Folder Browser ===
    
    @Slot()
    def browse_btn_clicked(self):
        self.browse_btn.disable_button()

        input_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder")
        if input_path:
            self.path_input_box.setText(input_path)

        self.browse_btn.enable_button()

# === Image Search Subprocess ===
    
    @Slot()
    def search_btn_clicked(self):
        """Runs image search and populates table in GUI."""
        self.search_btn.disable_button()

        path = self.return_search_path()
        begin_search = path and not getattr(self, "self._running", False)

        if begin_search:
            self._running = True
            self.update_status(f"Searching: {path}")
            self.run_search(path)
            self.configure_table_widget()

        self.search_btn.enable_button()


    def configure_table_widget(self):
        """Populate table with image search result and adjust sizing."""
        if getattr(self, "_update_table", True):
            self.table_data = self.configure_table_info(self.data_dict)
            self.table_widget.populate_table(self.table_data)
            self.adjust_table_size()
            self.show_table()


    def run_search(self, path=None):
        """Run search subprocess."""
        try:
            search_process = self.execute_subprocess(path)
            self.handle_process_output(search_process.stdout)
            self.data_dict = self.read_data()
        except Exception as e:
            mc.utils.warn(f"\n[SubprocessException] {str(e)}'")
            mc.utils.info(search_process.stdout)
        finally:
            self._running = False

    
    def execute_subprocess(self, path):
        """Execute and time search."""
        start_time = time.time()
        process = subprocess.run(
            ["python3.11", SCRIPT, path], capture_output=True,                        
            text=True, check=True)
        end_time = time.time()
        elapsed = end_time - start_time
        mc.utils.info(f"Subprocess time elapsed: {elapsed:.2f} seconds")
        return process
    

    def handle_process_output(self, process_output):
        """Read output from subprocess, handle errors."""
        self._process_info = self.read_feedback(process_output)
        self.find_errors(self._process_info)
        self.check_data_path(self._process_info)


    def find_errors(self, process_info: dict):
        """Read errors and raise excepctions."""
        for flag, msg in process_info.items():
            if flag == "InvalidPathError":
                self.handle_message(flag, msg, update=False)
                raise Exception(flag, msg)
            elif flag == "NoTargetFiles":
                self.handle_message(flag, msg, update=False)
                raise Exception(flag, msg)
            elif flag == "MaxFileError":
                self.handle_message(flag, msg, update=False)
                raise Exception(flag, msg)
            elif flag == "ZeroFileError":
                self.handle_message(flag, msg, update=False)
                raise Exception(flag, msg)
            elif flag == "MetadataError":
                self.handle_message(flag, msg, update=False)
                raise Exception(flag, msg)
            
    
    def check_data_path(self, process_info: dict):
        """Check data file with image search result."""
        if process_info["DataPath"]:
            data_path = Path(process_info["DataPath"])
            if data_path.exists():
                msg = f"Loading: {str(data_path)}"
                self.handle_message("[DataPath]", msg, update=True)
                self.clean_up_data()
                self._data_source = data_path
            else:
                raise Exception("[ErrorPathRead] failed to find path")

    
    def read_feedback(self, stdout: str):
        """Read stdout from subprocess."""
        output = stdout.strip().splitlines()
        ignore_flags = ["DEBUG", "INFO"]
        process_info = {line.split("] ")[0][1:]: line.split("] ", 1)[1] 
                            for line in output
                            if line.split("] ")[0][1:] 
                            not in ignore_flags}
        return process_info
        

    def handle_message(self, flag, message: str, update: bool):
        """Display and log subproccess messages."""
        self.update_status(f"{flag} {message}")
        mc.utils.info(f"{flag} {message}")
        self._update_table = update
                    
# === Import Images to Nodes ===

    @Slot()
    def import_btn_selected(self):
        self.import_btn.disable_button()

        if self._data_source == None:
            self.update_status("No data loaded or selected")
        
        data = self.get_selected_data()

        if self.data_loaded(data):
            self.get_or_set_attr("_import_num")

            backdrop = Backdrop(data, self._import_num)
            if backdrop.num == 2:
                backdrop.backdrop2 = True
                backdrop2 = Backdrop(data, self._import_num, 2)
            
            for node_num, image_info in enumerate(data):
                try:
                    paint_node = PaintNode(image_info)
                    adjust_y_axis_attr(paint_node, node_num, paint_node.h)
                    
                    if image_info["Broadcaster"]:
                        bcaster = BroadcasterNode(paint_node)
                        adjust_y_axis_attr(bcaster, node_num, paint_node.h)
                        backdrop.nodes_with_broadcaster.append(paint_node)
                        backdrop.nodes_with_broadcaster.append(bcaster)
                    else:
                        backdrop.nodes_without_broadcaster.append(paint_node)
                        
                    if backdrop.backdrop2:
                        backdrop.set_backdrop_postion_and_size(backdrop.nodes_with_broadcaster)
                        backdrop2.set_backdrop_postion_and_size(backdrop.nodes_without_broadcaster)
                    else:
                        node_lists_combined = backdrop.nodes_with_broadcaster + backdrop.nodes_without_broadcaster
                        backdrop.set_backdrop_postion_and_size(node_lists_combined)     
                    
                    paint_node.import_images_to_node()
                except Exception as e:
                    mari.utils.warn(e)
                    self.update_status(str(e))
        
        self.import_btn.enable_button()

    
    def get_or_set_attr(self, attr):
        """Set 1 if not exists, increment by 1 if exists"""
        setattr(self, attr, getattr(self, attr, 0) + 1)


    def data_loaded(self, data):
        data_loaded = True if data else False
        if not data_loaded:
            mc.utils.info("[Info] Data not loaded.")
        return data_loaded

# === Data Config / Cleaning ===

    def return_search_path(self):
        """Input handling for text entered into search box."""
        try:
            input_path = self.path_input_box.text()
            path = Path(input_path.strip())
            mc.utils.info(f"Checking: {str(path)}")
            if path.exists() and path != Path("."):
                mc.utils.info(f"Valid path: {str(path)}")
                self._input_path = str(path)
                return str(path)
            else:
                raise Exception(f"Path '{input_path}' invalid")
        except Exception as e:
            mc.utils.warn("[ERROR]", e)
            self.update_status(str(e))
            return None


    def configure_table_info(self, image_info: dict=None) -> list:
        """Dictonary formatted for displaying in GUI."""
        if not image_info:
            return

        entries = []
        for image_name, file_types in image_info.items():
            for etype, dict_list in file_types.items():
                for i in dict_list:
                    colourspace = "scalar" if i.get("channels", 0) == 1 else "color"
                    entries.append({
                        "Name": image_name,
                        "File Type": etype.upper(),
                        "Udim Count": len(dict_list),
                        "Size": i.get("res"),
                        "Depth": f"{i.get('bitdepth')}-bit",
                        "Colourspace": colourspace
                        })
                    break 
        return entries


    def get_selected_data(self):
        """Returns data from selected rows in GUI."""
        all_row_data = []

        for row_num in range(self.table_widget.rowCount()):
            row_data = {}
            for col_num in range(1, self.table_widget.columnCount()):
                header = self.table_widget.horizontalHeaderItem(col_num).text()
                checkbox = self.table_widget.item(row_num, 0)
                
                if checkbox.checkState() == Qt.Checked:
                    table_item = self.table_widget.item(row_num, col_num)
                    widget_item = self.table_widget.cellWidget(row_num, col_num)
                    
                    if widget_item is not None:
                        if isinstance(widget_item, QtWidgets.QCheckBox):
                            row_data[header] = widget_item.isChecked()
                        else:
                            row_data[header] = widget_item.currentText()
                    else:
                        row_data[header] = table_item.text()
            
            if row_data:
                paths = self.get_selected_image_paths(str(row_data["Name"]))
                row_data["files"] = paths
                all_row_data.append(row_data)

                
        all_row_data = self.get_indexes_for_node_placement(all_row_data)
        return all_row_data
    

    def get_indexes_for_node_placement(self, data: list):
        """Append different indexes for placement on seperate
        backdrops, depending on if node has broadcaster or not."""
        paint_nodes_w_broadcasters = [d for d in data if d["Broadcaster"]]
        for num, node in enumerate(paint_nodes_w_broadcasters):
            node["paint_node_indx"] = 0
            node["index"] = num

        paint_nodes = [d for d in data if not d["Broadcaster"]]
        for num, node in enumerate(paint_nodes):
            node["paint_node_indx"] = num
            node["index"] = 0
        return data
    

    def select_all_broadcaster(self):
        """Select all checkboxes, uncheck if
        all boxes selected."""
        table = self.table_widget
        row_count = table.rowCount()
        check_all = self.check_checkstate(7)
        for row in range(row_count):
            checkbox = table.cellWidget(row, 7)
            if check_all:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)


    def select_all_checkboxes(self):
        """Select all checkboxes if button clicked. 
        Uncheck if all boxes checked."""
        table = self.table_widget
        row_count = table.rowCount()
        check_all = self.check_checkstate(0)
        for row in range(row_count):
            checkbox = table.item(row, 0)
            if check_all:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)


    def check_checkstate(self, column: int) -> bool:
        """Check all boxes if any boxes are unchecked."""
        table = self.table_widget
        row_count = table.rowCount()
        unchecked = 0
        for row in range(row_count):
            if column == 0:
                checkbox = table.item(row, column)
                unchecked += 1 if checkbox.checkState() == Qt.Unchecked else 0
            elif column ==  7:
                checkbox = table.cellWidget(row, column)
                unchecked += 1 if not checkbox.isChecked() else 0
        return True if unchecked != 0 else False
    

    def get_selected_image_paths(self, name):
        """Add list of file paths to each selected row."""
        main_file_dict = self.data_dict
        filepaths = []
        for filename, data_dict in main_file_dict.items():
            if name == filename:
                for ext, data_list in data_dict.items():
                    for d in data_list:
                        filepaths.append(d["path"])
        return filepaths
    

    def read_data(self):
        """Read json created by image search for results."""
        try:
            json_file = self._data_source
            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                mc.utils.info(f"JSON file loaded: {json_file}")
                msg = f"Source: {self._input_path}"
                self.update_status(msg)
                return data
            
        except json.JSONDecodeError as e:
            mc.utils.info(f"Loading data error: {e}")
            return None
    

    def closeEvent(self, event):
        """Close application event."""
        self.clean_up_data()
        super().closeEvent(event)

    
    def clean_up_data(self):
        """Deletes current data source saved in
        temp files."""
        if hasattr(self, "_data_source") and self._data_source:
            path = Path(self._data_source)
            if path.exists():
                try:
                    path.unlink()
                    mc.utils.info(f"[CLEAN] Deleted: {path}")
                except Exception as e:
                    mc.utils.info(f"[ERROR] Failed to delete path: {path} {e}")

# === Mari Classes ===

class PaintNode:
    def __init__(self, selected_data: dict):
        data = selected_data
        self.data = data
        self.name = dict_value(data, 0)
        self.size = dict_value(data, 3)
        self.depth = dict_value(data, 4)
        self.space = dict_value(data, 5)
        self.broadcaster_value = dict_value(data, 6)
        self.source_files = dict_value(data, 7)
        self.paint_index = dict_value(data, 8)
        self.index = dict_value(data, 9)

        paint_node = self.create_paint_node()
        self.set_colourspace(paint_node)

        qsize = get_node_size(paint_node)
        self.w = qsize.width()
        self.h = qsize.height()
        self.x = 0 if self.broadcaster_value else -400

        self.qsize = qsize
        self.node = paint_node
        

    def create_paint_node(self) -> object:
        """Generate paint node on current node graph,
        using attributes from target import image set."""
        try:
            node_graph = mari.geo.current().nodeGraph()
            x, y = self.size.split("x")
            depth = self.depth.split('-')[0]
            paint_node = node_graph.createPaintNode(
                int(x), 
                int(y), 
                int(depth), 
                mari.Color(0.0))
            paint_node.setName(self.name) 
            return paint_node
        except Exception as e:
            mc.utils.info(f"Paint Node error {self.name}: {e}")
            raise Exception(f"Error creating node '{self.name}': {e}")

    
    def set_colourspace(self, node):
        """Set colourspace to either scalar or raw."""
        myconfig = node.colorspaceConfig()
        if self.space == "scalar":
            myconfig.setScalar(True)
        else:
            myconfig.setRaw(True)
        node.setColorspaceConfig(myconfig)


    def import_images_to_node(self):
        """Import image set to paint node."""
        image_template = self.get_template(self.data)
        image_set = self.node.imageSet()
        image_set.importImages(image_template, mari.ImageSet.SCALE_THE_PATCH)

    
    def get_template(self, data: dict) -> str:
        """Return template for importing imgas to node."""
        img_path = data["files"][0]
        f = TXT_REGEX.match(os.path.basename(img_path))
        name, sep, ext = f.group("name"), f.group("sep"), f.group("ext")
        template = f"{os.path.dirname(img_path)}/{name}{sep}$UDIM.{ext}"
        return template  


class BroadcasterNode:
    def __init__(self, paint_node: object):
        target_node = paint_node
        
        node = self.create_broadcast_node()
        broadcaster = self.set_name(node, target_node)
        self.connect_nodes(broadcaster, target_node.node)
        
        qsize = get_node_size(broadcaster)
        self.w = qsize.width()
        self.h = qsize.height()
        self.x = target_node.w * 2

        self.qsize = qsize
        self.broadcaster_value = True
        self.index = target_node.index
        self.target_node = target_node
        self.node = broadcaster

    
    def create_broadcast_node(self) -> object:
        """Create broadcaster node on current node graph."""
        node_graph = mari.geo.current().nodeGraph()
        broadcaster = node_graph.createNode("Misc/Teleport Broadcast")
        return broadcaster
    

    def set_name(self, broadcaster, paint_node):
        try:
            broadcaster.setName("Broadcaster")
            node_name = paint_node.name
            broadcaster.setChannelName(node_name)
            return broadcaster
        except ValueError as e:
            # Maybe do this outside class so you can offset where node 
            # lands on graph etc.
            broadcaster.setChannelName(node_name + f" {time_stamp()}")
            mc.utils.info(f"Error: duplicate broadcaster name for channel '{e}'")
            return broadcaster

    
    def connect_nodes(self, broadcaster:object, paint_node:object):
        """Connect paint node to broadcaster node."""
        broadcaster.setInputNode("Input", paint_node)


class Backdrop:
    def __init__(self, data:list, import_num, backdrop_num=None):
        self.backdrop_created = False
        self.num = self.backdrop_num(data)
        self.nodes_without_broadcaster = []
        self.nodes_with_broadcaster = []
        self.backdrop2 = False
        self.is_backdrop_2 = True if backdrop_num == 2 else False
        self.import_num = import_num


    def backdrop_num(self, data):
        backdrop_amount = set([d["Broadcaster"] for d in data])
        return len(backdrop_amount)


    def create_backdrop(self) -> object:
        node_graph = mari.geo.current().nodeGraph()
        backdrop = node_graph.createNode("Misc/Backdrop")
        backdrop.setName(f"Import Batch: {self.import_num} ({time_stamp()})")
        return backdrop
    

    def get_uniq_tag(self):
        unique_tag = f"import backdrop {time_stamp()}"
        return unique_tag
    

    def set_backdrop_postion_and_size(self, nodes:list):
        try:
            left = min(n.x for n in nodes)
            top = min(n.y for n in nodes)
            right = max(n.x + n.w for n in nodes) 
            bottom = max(n.y + n.h for n in nodes)

            XPADDING = 50
            YPADDING = 50
            width = XPADDING + (right - left) + XPADDING
            height = YPADDING + (bottom - top) + YPADDING

            qpointf = QPointF(left - XPADDING, top - YPADDING)

            if not getattr(self, "backdrop_created"):
                backdrop = self.create_backdrop()
                unique_tag = self.get_uniq_tag()
                backdrop.addTag(unique_tag)
                self.node = backdrop
                self.backdrop_created = True

            set_node_size(self.node, width, height)
            set_node_position(self.node, qpointf)
        except Exception as e:
            mc.utils.info(f"Skipping: {e}")

# === Misc Global Helpers ===

def adjust_y_axis_attr(node: object, node_num: int, add_y:float=118):
    """Set node y positon and then increase each time adjusting postion
    down the node graph."""
    if node_num == 0:
        node.y = 0
    else:
        if not node.broadcaster_value:
            if node.paint_index == 0:
                node.y = 0
            else:
                node.y = (add_y * node.paint_index) * 2
        else:
            node.y = (add_y * node.index) * 2
    
    qpointf = QPointF(node.x, node.y)
    set_node_position(node.node, qpointf)


def set_node_position(input_node, qpointf):
    input_node.setNodeGraphPosition(qpointf)


def get_node_size(node):
    if node:
        node_qsizef = node.nodeGraphSize()
    else:
        node_qsizef = None
    return node_qsizef


def set_node_size(node, width: float, height: float, qsizef=None):
    if not qsizef:
        qsizef = QSizeF(width, height)
    node.setNodeGraphSize(qsizef)


def time_stamp():
    timestamp = datetime.now().strftime("%Y%m%d")
    return timestamp


def dict_value(data: dict, index: int):
    value = list(data.values())[index]
    return value


# === Main Execution ===
    
if __name__ == "__main__":
    __window = MainWindow()
    __window.setWindowFlags(__window.windowFlags() | Qt.WindowStaysOnTopHint)
    __window.show()
    