import json
import requests
import shutil
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QLineEdit, QDialog, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QPixmap

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

CONFIG_FILE = os.path.join(os.path.dirname(sys.argv[0]), "config.json")
README_PATH = os.path.join(os.path.dirname(sys.argv[0]), "readme.md")

class ModrinthResultWidget(QWidget):
    def __init__(self, mod_data, install_callback):
        super().__init__()
        self.mod_data = mod_data
        layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setScaledContents(True)
        icon_url = mod_data.get("icon_url")
        if icon_url:
            try:
                img_data = requests.get(icon_url).content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                icon_label.setPixmap(pixmap)
            except:
                pass
        layout.addWidget(icon_label)

        info_layout = QVBoxLayout()
        title = QLabel(f"<b>{mod_data['title']}</b>")
        desc = QLabel(mod_data['description'][:100] + "...")
        desc.setWordWrap(True)
        info_layout.addWidget(title)
        info_layout.addWidget(desc)
        layout.addLayout(info_layout)

        install_button = QPushButton("Install")
        install_button.clicked.connect(lambda: install_callback(mod_data))
        layout.addWidget(install_button)

        self.setLayout(layout)

class ModInstaller(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Mod Installer")
        self.setFixedSize(600, 500)

        layout = QVBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("assets/logo.png"))
        logo_label.setPixmap(logo_pixmap.scaledToHeight(240, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        cgr_label = QLabel()
        cgr_pixmap = QPixmap(resource_path("assets/buildercgr.png"))
        cgr_label.setPixmap(cgr_pixmap.scaledToHeight(160, Qt.SmoothTransformation))
        cgr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(cgr_label)

        self.label = QLabel("Minecraft mods folder:")
        layout.addWidget(self.label)

        path_layout = QHBoxLayout()
        self.path_entry = QLineEdit()
        default_minecraft_path = os.path.join(os.getenv("APPDATA"), ".minecraft")
        self.path_entry.setText(default_minecraft_path)
        path_layout.addWidget(self.path_entry)

        self.search_modrinth_button = QPushButton("Search mods on Modrinth")
        self.search_modrinth_button.clicked.connect(self.open_modrinth_search)
        path_layout.addWidget(self.search_modrinth_button)

        self.browse_button = QPushButton("Browse folders")
        self.browse_button.clicked.connect(self.select_folder)
        path_layout.addWidget(self.browse_button)

        layout.addLayout(path_layout)

        self.select_mods_button = QPushButton("Select .jar files")
        self.select_mods_button.clicked.connect(self.select_mod_jars)
        layout.addWidget(self.select_mods_button)

        self.install_button = QPushButton("Install mods from 'mods' folder")
        self.install_button.clicked.connect(self.install_mods_from_folder)
        layout.addWidget(self.install_button)

        self.setLayout(layout)
        self.selected_mods = []

        config = load_config()
        self.path_entry.setText(config.get("minecraft_path", self.path_entry.text()))

        self.help_button = QPushButton("Help")
        self.help_button.setToolTip("Open README.md")
        self.help_button.clicked.connect(self.open_readme)
        layout.addWidget(self.help_button)

    def open_readme(self):
        os.startfile(README_PATH)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Minecraft folder")
        if folder:
            self.path_entry.setText(folder)

    def select_mod_jars(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select .jar files",
            "",
            "JAR Files (*.jar)"
        )
        if files:
            self.selected_mods = files
            QMessageBox.information(self, "Mods selected", f"{len(files)} file(s) selected.")

    def install_mods_from_folder(self):
        minecraft_path = self.path_entry.text().strip()
        if not minecraft_path or not os.path.isdir(minecraft_path):
            QMessageBox.warning(self, "Error", "Please select a valid Minecraft folder.")
            return

        mods_folder = os.path.join(minecraft_path, "mods")
        if not os.path.exists(mods_folder):
            os.makedirs(mods_folder, exist_ok=True)

        for file in self.selected_mods:
            if file.endswith(".jar"):
                shutil.copy(file, mods_folder)

        if os.path.isdir("mods"):
            for file in os.listdir("mods"):
                if file.endswith(".jar"):
                    shutil.copy(os.path.join("mods", file), mods_folder)

        QMessageBox.information(self, "Success", "Mods installed successfully!")

    def open_modrinth_search(self):
        dialog = ModrinthSearchWindow(self)
        dialog.exec_()

class ModrinthSearchWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Search mods on Modrinth")
        self.setFixedSize(600, 500)
        self.parent = parent

        layout = QVBoxLayout()

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search mod...")
        layout.addWidget(self.search_entry)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

        self.setLayout(layout)
        self.mods_data = []

        self.loader_entry = QLineEdit()
        self.loader_entry.setPlaceholderText("Loader (forge, fabric, neoforge)")
        layout.addWidget(self.loader_entry)

        self.version_entry = QLineEdit()
        self.version_entry.setPlaceholderText("Minecraft version (e.g. 1.20.1)")
        layout.addWidget(self.version_entry)

        config = load_config()
        self.loader_entry.setText(config.get("modloader", ""))
        self.version_entry.setText(config.get("version", ""))

    def perform_search(self):
        query = self.search_entry.text().strip()
        loader = self.loader_entry.text().strip().lower()
        version = self.version_entry.text().strip()

        save_config({
            "modloader": self.loader_entry.text().strip(),
            "version": self.version_entry.text().strip(),
            "minecraft_path": self.parent.path_entry.text().strip()
        })

        facets = []
        if loader:
            facets.append([f"categories:{loader}"])
        if version:
            facets.append([f"versions:{version}"])

        url = "https://api.modrinth.com/v2/search"
        params = {
            "query": query,
            "facets": str(facets).replace("'", '"')
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            self.mods_data = response.json()["hits"]
            self.results_list.clear()
            for mod in self.mods_data:
                item = QListWidgetItem()
                widget = ModrinthResultWidget(mod, self.download_mod)
                item.setSizeHint(widget.sizeHint())
                self.results_list.addItem(item)
                self.results_list.setItemWidget(item, widget)

    def download_mod(self, mod):
        project_id = mod["project_id"]
        version_url = f"https://api.modrinth.com/v2/project/{project_id}/version"
        response = requests.get(version_url)
        if response.status_code != 200:
            QMessageBox.warning(self, "Error", "Could not retrieve mod version.")
            return

        versions = response.json()
        for v in versions:
            if "forge" in v["loaders"]:
                file_url = v["files"][0]["url"]
                filename = v["files"][0]["filename"]
                break
        else:
            QMessageBox.warning(self, "Error", "No compatible version found.")
            return

        minecraft_path = self.parent.path_entry.text().strip()
        mods_folder = os.path.join(minecraft_path, "mods")
        if not os.path.exists(mods_folder):
            os.makedirs(mods_folder, exist_ok=True)

        file_path = os.path.join(mods_folder, filename)
        with requests.get(file_url, stream=True) as r:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        QMessageBox.information(self, "Downloaded", f"{filename} installed successfully.")

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

if __name__ == "__main__":
    app = QApplication([])
    qss_path = resource_path("style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    window = ModInstaller()
    window.show()
    app.exec_()
