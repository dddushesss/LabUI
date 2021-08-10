import os
import re
import sys
import time

import fitz
import pyscreenshot
from PyQt5.QtWebEngineWidgets import QWebEngineSettings

from PyQt5 import QtWebEngineWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
import mouse

from qt import Ui_MainWindow


class App(QMainWindow, Ui_MainWindow):
    pageCount = 0
    imgs = []
    chosenPages = []
    textBoxChosenPages = []
    checkBoxes = []
    model = QtGui.QStandardItemModel()

    def __init__(self):
        super().__init__()
        self.pdfview = QtWebEngineWidgets.QWebEngineView()
        self.all_dates = {}
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        self.action.triggered.connect(self.screenShotPart)
        self.action_2.triggered.connect(self.screenShot)

        self.openFileButton.clicked.connect(self.add_file)
        self.verticalLayout.addWidget(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.pdfview)
        self.setAcceptDrops(True)
        self.listView.setModel(self.model)
        self.listView.clicked[QtCore.QModelIndex].connect(self.open_file_list)
        self.Delete.clicked.connect(self.deleteItem)

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.accept()
        else:
            event.ignore()

    def screenShot(self):
        self.hide()
        im = pyscreenshot.grab()
        im.save("screenshot.png")
        self.show()

    def screenShotPart(self):
        self.hide()

        while not mouse.is_pressed():
            time.sleep(0.1)
        mouseGrub = mouse.get_position()
        while mouse.is_pressed():
            time.sleep(0.1)
        mouseGrubExit = mouse.get_position()
        im = pyscreenshot.grab(bbox=(mouseGrub[0], mouseGrub[1], mouseGrubExit[0], mouseGrubExit[1]))
        im.save("screenshot.png")
        self.show()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f[-4:] == ".pdf":
                iteam = QtGui.QStandardItem(f)
                self.model.appendRow(iteam)

    def deleteItem(self):
        for index in self.listView.selectedIndexes():
            self.model.removeRow(index.row())
        if len(self.listView.selectedIndexes()) > 0:
            i = self.model.index(0, 0)
            self.listView.setCurrentIndex(i)
            self.open_file_list(i)
        else:
            self.verticalLayout.removeWidget(self.pdfview)
            self.pdfview = QtWebEngineWidgets.QWebEngineView()
            self.verticalLayout.addWidget(self.pdfview)

    def open_file_list(self, index):
        self.fname = self.model.itemFromIndex(index).text()
        if len(self.fname) > 0:
            pdf = "file:///" + self.fname
            self.pdfview.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            self.pdfview.load(QtCore.QUrl(pdf))
            self.lineEdit.textChanged[str].connect(self.OnLineEdit_web)
            self.pageCount = len(fitz.open(self.fname))
            self.ConvertButton.clicked.connect(self.Convert_web)

    def add_file(self):
        fname = QFileDialog.getOpenFileNames(self, 'Open file',
                                             'c:\\', "PDF (*.pdf)")

        if (len(fname[0]) > 0):
            for name in fname[0]:
                item = QtGui.QStandardItem(name)
                self.model.appendRow(item)

    def OnLineEdit_web(self):
        text = self.lineEdit.text()
        text = re.sub("\s", "", text)
        text = re.sub("--", "-", text)
        text = re.sub(",,", ",", text)
        text = re.sub(",-", "-", text)
        text = re.sub("-,", ",", text)

        if len(text) > 0 and not text[len(text) - 1].isdigit() and text[len(text) - 1] != ',' and text[
            len(text) - 1] != '-':
            text = text.replace(text[len(text) - 1], "")

        arr = re.split("[,-]", text)
        sep = re.split("[0-9]", text)
        while arr.__contains__(""):
            arr.remove("")
        while sep.__contains__(""):
            sep.remove("")
        while sep.__contains__("-"):
            sep.remove("-")

        i = 0

        self.chosenPages = []

        arr = re.split(",", text)
        while arr.__contains__(""):
            arr.remove("")
        for a in arr:
            a1 = re.split("-", a)
            while a1.__contains__(""):
                a1.remove("")
            if len(a1) == 1 and (int(a1[0]) > self.pageCount):
                arr.remove(a)
            elif len(a1) > 1 and (int(a1[0]) > self.pageCount or int(a1[1]) > self.pageCount):
                arr.remove(a)
            elif len(a1) > 1 and len(a1[1]) > 0 and int(a1[0]) < int(a1[1]):
                for j in range(int(a1[0]), int(a1[1]) + 1):
                    if not self.chosenPages.__contains__(j):
                        self.chosenPages.append(j)
            elif len(a1) > 1 and len(a1[1]) > 0 and int(a1[0]) >= int(a1[1]):
                for j in range(int(a1[1]), int(a1[0]) + 1):
                    if not self.chosenPages.__contains__(j):
                        self.chosenPages.append(j)
            else:
                if not self.chosenPages.__contains__(int(a1[0])):
                    self.chosenPages.append(int(a1[0]))
        text = ""
        for s in arr:
            if len(s) > 0:
                text += s
            if (len(sep) >= i + 1):
                text += sep[i]
            i += 1

        self.lineEdit.setText(text)
        self.textBrowser.setText("")
        for choise in self.chosenPages:
            self.textBrowser.append(str(choise))

    def Convert_web(self):
        folder = "result"
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        if (len(self.fname) > 2):
            pdf_document = fitz.open(self.fname)
            for current_page in self.chosenPages:
                for image in pdf_document.getPageImageList(current_page - 1):
                    xref = image[0]
                    try:
                        pix = fitz.Pixmap(pdf_document, xref)
                        if pix.n < 5:  # this is GRAY or RGB
                            pix.writePNG("result/%s.png" % (current_page - 1))
                        else:  # CMYK: convert to RGB first
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            pix1.writePNG("result/%s.png" % (current_page - 1))
                            pix1 = None
                        pix = None
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка",
                                            "Невозможно преобразовать страницу в картинку!\n" + e.args[0],
                                            QMessageBox.Ok)
                        return


def main():
    app = QApplication(sys.argv)
    window = App()

    window.show()
    app.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
