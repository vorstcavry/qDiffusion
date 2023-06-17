from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QThread, QMimeData, QByteArray
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import QImage, QDesktopServices, QDrag

import sql
import os
import PIL.Image
import misc
import re
import shutil
import time
import json
from misc import MimeData
from gui import MODEL_FOLDERS

LABELS =  {
    "favourite": "Favourites",
    "checkpoint": "Checkpoints",
    "component": "Components",
    "lora": "LoRAs",
    "hypernet": "Hypernets",
    "embedding": "Embeddings",
    "upscaler": "Upscalers",
    "wildcard": "Wildcards"
}
MODES = {v:k for k,v in LABELS.items()}

MIME_EXPLORER_MODEL = "application/x-qd-explorer-model"

class Populater(QObject):
    finished = pyqtSignal()
    def __init__(self, gui, name):
        super().__init__()
        self.gui = gui
        self.name = name
        self.conn = None

    @pyqtSlot()
    def populateOptions(self):
        self.gui.setTabWorking(self.name, True)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.enableNotifications("models")

        self.optionsUpdated()
        self.favouritesUpdated()

        self.gui.setTabWorking(self.name, False)
        self.finished.emit()

    @pyqtSlot()
    def populateFavourites(self):
        self.gui.setTabWorking(self.name, True)
        
        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.enableNotifications("models")

        self.favouritesUpdated()
        
        self.gui.setTabWorking(self.name, False)
    
    def setModel(self, name, category, display, type, idx, allow_folder = True):
        q = QSqlQuery(self.conn.db)

        file = os.path.abspath(os.path.join(self.gui.modelDirectory(), name))
        location = file.rsplit(".",1)[0]

        folder = ""
        parts = name.split(os.path.sep)
        if len(parts) > 2 and allow_folder:
            folder = parts[1]

        if os.path.exists(location + ".preview.png"):
            preview = location + ".preview.png"
        else:
            preview = location + ".png"
        
        w,h = 0,0
        if os.path.exists(preview):
            try:
                with PIL.Image.open(preview) as img:
                    w,h = img.size
            except:
                pass
        
        description = ""
        if os.path.exists(location + ".civitai.info"):
            with open(location + ".civitai.info", "r", encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    description = f"""
                        <p><b>Name</b>: {data['model']['name']}<br>
                        <b>Type</b>: {data['model']['type']}<br>
                        <b>Activation</b>: {', '.join(data['trainedWords'])}<br>
                        <b>Base model</b>: {data['baseModel']}<br>
                        <b>Description</b>: </p>{data['description']}
                    """
                except:
                    pass

        for ext in [".txt", ".csv"]:
            if os.path.exists(location + ext):
                with open(location + ext, "r", encoding='utf-8') as f:
                    description = f.read().strip()
        
        q.prepare("INSERT OR REPLACE INTO models(name, category, display, type, file, folder, desc, idx, width, height) VALUES (:name, :category, :display, :type, :file, :folder, :desc, :idx, :width, :height);")
        q.bindValue(":name", name)
        q.bindValue(":category", category)
        q.bindValue(":display", display)
        q.bindValue(":type", type)
        q.bindValue(":file", preview)
        q.bindValue(":folder", folder)
        q.bindValue(":desc", description)
        q.bindValue(":idx", idx)
        q.bindValue(":width", w)
        q.bindValue(":height", h)
        self.conn.doQuery(q)

    def finishCategory(self, category, total):
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM models WHERE category == :category AND idx >= :total;")
        q.bindValue(":category", category)
        q.bindValue(":total", total)
        self.conn.doQuery(q)

    def optionsUpdated(self):
        wildcards = self.gui.wildcards._wildcards
        for idx, name in enumerate(wildcards):
            file = os.path.join("WILDCARD", self.gui.wildcards._sources[name])
            self.setModel(file, "wildcard", "", "wildcard", idx)
        self.finishCategory("wildcard", len(wildcards))

        o = self.gui._options
        if not o:
            return
        
        checkpoints = [a for a in o["UNET"] if a in o["VAE"] and a in o["CLIP"]]
        for idx, name in enumerate(checkpoints):
            self.setModel(name, "checkpoint", "", "checkpoint", idx)
        self.finishCategory("checkpoint", len(checkpoints))
        
        components = [a for a in o["VAE"] if not a in checkpoints]
        for idx, name in enumerate(components):
            self.setModel(name, "component", "VAE", "component", idx)
        self.finishCategory("component", len(components))

        for idx, name in enumerate(o["LoRA"]):
            self.setModel(name, "lora", "", "lora", idx)
        self.finishCategory("lora", len(o["LoRA"]))
        
        for idx, name in enumerate(o["HN"]):
            self.setModel(name, "hypernet", "", "hypernet", idx)
        self.finishCategory("hypernet", len(o["HN"]))

        for idx, name in enumerate(o["TI"]):
            self.setModel(name, "embedding", "", "embedding", idx)
        self.finishCategory("embedding", len(o["TI"]))

        for idx, name in enumerate(o["SR"]):
            self.setModel(name, "upscaler", "", "upscaler", idx)
        self.finishCategory("upscaler", len(o["SR"]))

    def favouritesUpdated(self):
        f = self.gui._favourites
        idx = 0

        wildcards = [os.path.join("WILDCARD", self.gui.wildcards._sources[name]) for name in self.gui.wildcards._wildcards]        
        for name in [a for a in wildcards if a in f]:
            self.setModel(name, "favourite", "Wildcard", "wildcard", idx, False)
            idx += 1

        if not self.gui._options:
            self.finishCategory("favourite", idx)
            return
        
        o = self.gui._options.copy()
        for k in list(o.keys()):
            if type(o[k]) == list:
                o[k] = [a for a in o[k] if a in f]

        checkpoints = [a for a in o["UNET"] if a in o["VAE"] and a in o["CLIP"]]
        for name in checkpoints:
            self.setModel(name, "favourite", "Checkpoint", "checkpoint", idx, False)
            idx += 1

        for name in [a for a in o["VAE"] if not a in checkpoints]:
            self.setModel(name, "favourite", "VAE", "component", idx, False)
            idx += 1

        for name in o["LoRA"]:
            self.setModel(name, "favourite", "LoRA", "lora", idx, False)
            idx += 1
        
        for name in o["HN"]:
            self.setModel(name, "favourite", "Hypenet", "hypernet", idx, False)
            idx += 1

        for name in o["TI"]:
            self.setModel(name, "favourite", "Embedding", "embedding", idx, False)
            idx += 1

        for name in o["SR"]:
            self.setModel(name, "favourite", "Upscaler", "upscaler", idx, False)
            idx += 1

        self.finishCategory("favourite", idx)


class Explorer(QObject):
    updated = pyqtSignal()
    tabUpdated = pyqtSignal()
    updateOptions = pyqtSignal()
    updateFavourites = pyqtSignal()
    dragSignal = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.priority = 1
        self.name = "Models"
        self.gui = parent
        self.populater = Populater(self.gui, self.name)
        self.populaterThread = QThread()
        self.populater.moveToThread(self.populaterThread)
        self.updateOptions.connect(self.populater.populateOptions)
        self.updateFavourites.connect(self.populater.populateFavourites)
        self.populater.finished.connect(self.finished)
        self.populaterThread.start()
        self.optionsRunning = False
        self.optionsOutdated = False

        qmlRegisterSingletonType(Explorer, "gui", 1, 0, "EXPLORER", lambda qml, js: self)

        self.gui.optionsUpdated.connect(self.optionsUpdated)
        self.gui.favUpdated.connect(self.favouritesUpdated)
        self.gui.aboutToQuit.connect(self.stop)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE models(name TEXT, category TEXT, display TEXT, type TEXT, file TEXT, folder TEXT, desc TEXT, idx INTEGER, width INTEGER, height INTEGER, CONSTRAINT unq UNIQUE (category, idx));")
    
        self._currentTab = "favourite"
        self._currentFolder = ""
        self._cellSize = 150
        self._showInfo = False

        self.dragSignal.connect(self.drag, Qt.QueuedConnection)

    @pyqtProperty(str, notify=tabUpdated)
    def currentTab(self): 
        return self._currentTab
    
    @currentTab.setter
    def currentTab(self, tab):
        self._currentTab = tab
        self._currentFolder = ""
        self.tabUpdated.emit()

    @pyqtProperty(str, notify=tabUpdated)
    def currentFolder(self): 
        return self._currentFolder
    
    @currentFolder.setter
    def currentFolder(self, folder):
        self._currentFolder = folder
        self.tabUpdated.emit()

    @pyqtSlot(str, result=str)
    def getLabel(self, mode):
        return LABELS[mode]
    
    @pyqtSlot(str, result=str)
    def getMode(self, label):
        return MODES[label]

    @pyqtSlot()
    def stop(self):
        self.populaterThread.quit()
        self.populaterThread.wait()

    @pyqtSlot()
    def optionsUpdated(self):
        if self.optionsRunning:
            self.optionsOutdated = True
            return
        self.optionsRunning = True
        self.updateOptions.emit()

    @pyqtSlot()
    def favouritesUpdated(self):
        self.updateFavourites.emit()

    @pyqtSlot()
    def finished(self):
        self.optionsRunning = False
        if self.optionsOutdated:
            self.optionsOutdated = False
            self.optionsUpdated()

    @pyqtSlot(misc.MimeData, str)
    def doReplace(self, mimedata, file):
        mimedata = mimedata.mimeData
        image = None
        if mimedata.hasImage():
            image = mimedata.imageData()
            if image and not image.isNull():
                image.save(file)

        for url in mimedata.urls():
            if url.isLocalFile():
                image = QImage(url.toLocalFile())
                break
        
        if image:
            os.makedirs(os.path.dirname(file), exist_ok=True)
            image.save(file)
            self.gui.thumbnails.remove(file)
            self.gui.watchModelDirectory()
            
    @pyqtSlot(str)
    def doClear(self, file):
        if os.path.exists(file):
            os.remove(file)
            self.gui.thumbnails.remove(file)

    @pyqtSlot(str)
    def doDelete(self, file):
        request = {"type":"manage", "data": {"operation": "modify", "old_file": file, "new_file": ""}}
        self.gui.makeRequest(request)

    @pyqtSlot(str)
    def doPrune(self, file):
        request = {"type":"manage", "data": {"operation": "prune", "file": file}}
        self.gui.makeRequest(request)

    @pyqtSlot(str)
    def doVisit(self, file):
        path = os.path.abspath(os.path.join(self.gui.modelDirectory(), file))
        try:
            self.gui.visitFiles([path])
        except Exception:
            pass

    @pyqtSlot(str, str, str)
    def doEdit(self, file, name, desc):
        old_file = file
        new_file = os.path.join(os.path.dirname(old_file), name)
        old_path = os.path.abspath(os.path.join(self.gui.modelDirectory(), old_file.split('.',1)[0]))
        new_path = os.path.abspath(os.path.join(self.gui.modelDirectory(), new_file.split('.',1)[0]))

        if old_file != new_file:
            if os.path.exists(old_path + ".txt"):
                shutil.move(old_path + ".txt", new_path + ".txt")
            if os.path.exists(old_path + ".png"):
                shutil.move(old_path + ".png", new_path + ".png")

        if desc:
            with open(new_path + ".txt", "w", encoding='utf-8') as f:
                f.write(desc)
        elif os.path.exists(new_path + ".txt"):
            os.remove(new_path + ".txt")

        if old_file != new_file:
            request = {"type":"manage", "data": {"operation": "modify", "old_file": old_file, "new_file": new_file}}
            self.gui.makeRequest(request)

        self.optionsUpdated()

    @pyqtSlot(str)
    def drag(self, model):
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setData(MIME_EXPLORER_MODEL, QByteArray(model.encode()))
        drag.setMimeData(mimeData)
        drag.exec()

    @pyqtSlot(str)
    def doDrag(self, model):
        self.dragSignal.emit(model)

    @pyqtSlot(MimeData, result=str)
    def onDrop(self, mimeData):
        mimeData = mimeData.mimeData
        if MIME_EXPLORER_MODEL in mimeData.formats():
            return str(mimeData.data(MIME_EXPLORER_MODEL), 'utf-8')
        else:
            return ""
    
    @pyqtSlot(str, str, str)
    def doMove(self, model, folder, subfolder):
        folder = MODEL_FOLDERS[folder][0]
        request = {"type":"manage", "data": {"operation": "move", "old_file": model, "new_folder": folder, "new_subfolder": subfolder}}
        self.gui.makeRequest(request)

    @pyqtProperty(int, notify=updated)
    def cellSize(self):
        return self._cellSize

    @pyqtSlot(int)
    def adjustCellSize(self, adj):
        cellSize = self._cellSize + adj
        if cellSize >= 150 and cellSize <= 450:
            self._cellSize = cellSize
            self.updated.emit()

    @pyqtProperty(bool, notify=updated)
    def showInfo(self):
        return self._showInfo
    
    @showInfo.setter
    def showInfo(self, showInfo):
        self._showInfo = showInfo
        self.updated.emit()
