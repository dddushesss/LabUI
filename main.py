import os
import re
import sys

import fitz
from PyQt5 import QtWebEngineWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QCheckBox

from qt import Ui_MainWindow


class App(QMainWindow, Ui_MainWindow):
    pageCount = 0
    imgs = []
    chosenPages = []
    textBoxChosenPages = []
    checkBoxes = []
    PDFJS = 'file:///PdfJS/web/viewer.html'
    model = QtGui.QStandardItemModel()

    def __init__(self):
        super().__init__()
        self.all_dates = {}
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("sad")
        self.openFileButton.clicked.connect(self.add_file)
        self.verticalLayout.addWidget(self.verticalLayoutWidget)
        self.pdfview = QtWebEngineWidgets.QWebEngineView()
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

    def add_Image(self, Image):
        lay = self.verticalLayout
        lbl = QLabel(self)
        pixmap = QPixmap()
        pixmap.load(Image)
        pixmapResized = pixmap.scaledToWidth(500)
        lbl.setPixmap(pixmapResized)
        lay.addWidget(lbl)
        box = QCheckBox(re.sub("tmp/", "", re.sub(".png", "", Image)), self)
        box.stateChanged.connect(self.CheckBoxStateChanged)

        box.setObjectName(box.text())
        self.checkBoxes.append(box)
        lay.addWidget(box)

    def open_file_list(self, index):
        fname = self.model.itemFromIndex(index).text()
        if (len(fname) > 0):
            pdf = "file:///" + fname
            self.verticalLayout.itemAt(0).widget().load(QtCore.QUrl.fromUserInput('%s?file=%s' % (self.PDFJS, pdf)))
            self.lineEdit.textChanged[str].connect(self.OnLineEdit_web)
            self.pageCount = len(fitz.open(fname))
            self.ConvertButton.clicked.connect(lambda: self.Convert_web(fname))

    def open_file_handly(self, fname):
        self.ConvertButton.clicked.connect(self.Convert)
        folder = 'tmp'
        self.lineEdit.textChanged[str].connect(self.OnLineEdit)
        for i in range(0, self.verticalLayout.count()):
            self.verticalLayout.itemAt(i).widget().deleteLater()
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        if (len(fname[0]) > 2):
            doc = fitz.open(fname[0])

            for i in range(1, len(doc)):
                for img in doc.getPageImageList(i):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:  # this is GRAY or RGB
                        pix.writePNG("tmp/%s.png" % (i))
                    else:  # CMYK: convert to RGB first
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        pix1.writePNG("tmp/%s.png" % (i))
                        pix1 = None
                    pix = None

            for i in range(1, len(doc)):
                self.add_Image("tmp/" + str(i) + ".png")

            self.pageCount = len(doc)

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
        while (arr.__contains__("")):
            arr.remove("")
        while (sep.__contains__("")):
            sep.remove("")
        while (sep.__contains__("-")):
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
                    if (not self.chosenPages.__contains__(j)):
                        self.chosenPages.append(j)
            elif len(a1) > 1 and len(a1[1]) > 0 and int(a1[0]) >= int(a1[1]):
                for j in range(int(a1[1]), int(a1[0]) + 1):
                    if (not self.chosenPages.__contains__(j)):
                        self.chosenPages.append(j)
            else:
                if (not self.chosenPages.__contains__(int(a1[0]))):
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

    def Convert_web(self, fname):
        folder = "result"
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        if (len(fname) > 2):
            doc = fitz.open(fname)
            for i in self.chosenPages:
                for img in doc.getPageImageList(i):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:  # this is GRAY or RGB
                        pix.writePNG("result/%s.png" % (i))
                    else:  # CMYK: convert to RGB first
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        pix1.writePNG("result/%s.png" % (i))
                        pix1 = None
                    pix = None


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
