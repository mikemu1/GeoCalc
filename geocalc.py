import sys
from time import localtime, strftime

from PyQt5.QtWidgets import QWidget, QApplication, QShortcut
from PyQt5.QtWidgets import QLabel, QLineEdit, QComboBox
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout
from PyQt5.QtWidgets import QPushButton, QMessageBox, QGroupBox
from PyQt5.QtGui import QPixmap, QFont, QKeySequence
from PyQt5.QtCore import Qt

from gengine import Location, GeoPath
from gengine import radius_model, rhumb, greatcircle, keepd
import style

GVERSION = '10.4'


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Distance & Bearing")
        self.setGeometry(150, 150, 425, 700)
        self.setStyleSheet("font: 16pt")
        self.ui()
        # self.widget_dict = vars(self)  # capture all widgets in layout
        self.show()
        self.enterFromLocation.setFocus()   # Start entry @ from location

    def ui(self):
        self.widgets()
        self.layouts()
        # Keyboard shortcut ctrl-Q to close
        self.quitSc = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.quitSc.activated.connect(self.close)

    def widgets(self):
        self.lblImg = QLabel()
        self.lblImg.setPixmap(QPixmap("Images/sphere.png"))
        self.lblGeo = QLabel("GeoCalc ")
        self.lblGeo.setFont(QFont('Eurostile', 16))
        self.lblGeo.setStyleSheet('font-weight: Bold; font-size: 54pt')
        self.lblGeo.setStyleSheet('color: blue')
        self.cbxEllipse = QComboBox()
        self.cbxEllipse.addItems(['WGS-84', 'Sphere'])
        self.cbxEllipse.setStyleSheet('font-size: 10pt')
        self.cbxEllipse.setEditable(False)
        self.cbxEllipse.setInsertPolicy(0)
        self.enterFromLocation = QLineEdit()
        self.enterFromLat = QLineEdit()
        self.enterFromLat.setPlaceholderText("±DD.ddddd")
        self.enterFromLon = QLineEdit()
        self.enterFromLon.setPlaceholderText("DD MM SS.ss N")
        self.enterToLocation = QLineEdit()
        self.enterToLat = QLineEdit()
        self.enterToLon = QLineEdit()
        self.btnHome = QPushButton("Home")
        self.btnHome.clicked.connect(self.do_home)
        self.btnCalc = QPushButton("Calculate")
        self.btnCalc.clicked.connect(self.do_calc)
        self.btnClear = QPushButton("Clear")
        self.btnClear.clicked.connect(self.do_clear)
        self.rhumbDistance = QLineEdit()
        # print(self.enterFromLat.objectName())
        self.rhumbBearing = QLineEdit()
        self.gcDistance = QLineEdit()
        self.gcBearing = QLineEdit()
        self.rhumbDistance.setReadOnly(True)
        self.rhumbBearing.setReadOnly(True)
        self.gcDistance.setReadOnly(True)
        self.gcBearing.setReadOnly(True)
        self.btnSave = QPushButton("Save")
        self.btnSave.clicked.connect(self.do_save)
        self.btnQuit = QPushButton("Quit")
        self.btnQuit.setStyleSheet("color: red; font: Bold")
        self.btnQuit.clicked.connect(self.close)
        self.lblVers = QLabel(GVERSION)
        self.lblVers.setStyleSheet('font-size: 10pt')

    def layouts(self):
        # ------ Layout stack -----------------------
        self.mainLayout = QVBoxLayout()
        self.headerLayout = QHBoxLayout()
        self.inMainLayout = QVBoxLayout()
        self.inButtonLayout = QHBoxLayout()
        self.outMainLayout = QVBoxLayout()
        self.outButtonLayout = QHBoxLayout()
        self.revLayout = QHBoxLayout()

        # -------- header ----------------------------
        self.headerLayout.addWidget(self.lblImg)
        self.headerLayout.addWidget(self.lblGeo)

        # -------- input groupbox --------------------
        self.inGroupBox = QGroupBox("Input")
        self.inGroupBox.setStyleSheet(style.groupboxStyle())
        self.inLayout = QFormLayout()
        self.inLayout.setLabelAlignment(Qt.AlignLeft)
        self.inLayout.addRow("", self.cbxEllipse)
        self.inLayout.addRow("From Location: ", self.enterFromLocation)
        self.inLayout.addRow("From Latitude: ", self.enterFromLat)
        self.inLayout.addRow("From Longitude: ", self.enterFromLon)
        self.inLayout.addRow("To Location: ", self.enterToLocation)
        self.inLayout.addRow("To Latitude: ", self.enterToLat)
        self.inLayout.addRow("To Longitude: ", self.enterToLon)

        self.inButtonLayout.addStretch()
        self.inButtonLayout.addWidget(self.btnHome)
        self.inButtonLayout.addWidget(self.btnCalc)
        self.inButtonLayout.addWidget(self.btnClear)
        self.inButtonLayout.addStretch()

        # -------- output groupbox -------------------
        self.outGroupBox = QGroupBox("Output")
        self.outGroupBox.setStyleSheet(style.groupboxStyle())
        self.outLayout = QFormLayout()
        self.outLayout.setLabelAlignment(Qt.AlignLeft)
        self.outLayout.addRow("", QLabel(""))
        self.outLayout.addRow("Rhumb Line Distance: ", self.rhumbDistance)
        self.outLayout.addRow("Rhumb Line Bearing: ", self.rhumbBearing)
        self.outLayout.addRow("Great Circle Distance: ", self.gcDistance)
        self.outLayout.addRow("GC Initial Course: ", self.gcBearing)

        self.outButtonLayout.addStretch()
        self.outButtonLayout.addWidget(self.btnSave)
        self.outButtonLayout.addWidget(self.btnQuit)
        self.outButtonLayout.addStretch()

        # -------- assemble nested layouts ---------------
        self.mainLayout.addLayout(self.headerLayout)
        self.inMainLayout.addLayout(self.inLayout)
        self.inMainLayout.addLayout(self.inButtonLayout)
        self.inGroupBox.setLayout(self.inMainLayout)
        self.mainLayout.addWidget(self.inGroupBox)
        self.outMainLayout.addLayout(self.outLayout)
        self.outMainLayout.addLayout(self.outButtonLayout)
        self.outGroupBox.setLayout(self.outMainLayout)
        self.mainLayout.addWidget(self.outGroupBox)
        self.mainLayout.addLayout(self.revLayout)

        self.revLayout.addStretch()
        self.revLayout.addWidget(self.lblVers)
        self.revLayout.addStretch()
        # -------- final setlayout ------------
        self.setLayout(self.mainLayout)

    def do_clear(self):
        # reset inputs
        self.enterFromLat.clear()
        self.enterFromLon.clear()
        self.enterToLat.clear()
        self.enterToLon.clear()
        # clear outputs
        self.rhumbDistance.clear()
        self.rhumbBearing.clear()
        self.gcDistance.clear()
        self.gcBearing.clear()

    def do_home(self) -> None:
        '''
        Intended to fill-in From entry fields with values for HOME
        Used initially to fill-in all fields to simplify testing
        '''
        self.enterFromLocation.setText('Home')
        self.enterFromLat.setText('45.5361')
        self.enterFromLon.setText('-122.8092')
        # self.enterToLocation.setText('Jon')
        # self.enterToLat.setText('42.9514')
        # self.enterToLon.setText('-85.4311')

    def parse_entry(self, le: object, id: str) -> bool:
        '''
        Check From/To Lat/Lon entry fields
        Convert Degree-Minutes-Seconds-NESW to +/- degrees (float)
        Empty entries send message and return False
        Indecipherable entries send message and return False
        Latitudes North of Equator are positive
        Longitudes East of Prime Meridian (Greenwich) are positive
        '''
        ddstring: str = le.text()
        if not ddstring:        # zero-length string
            self.mbox("No " + id + " input", "Calculations STOP")
            return False
        ending: str = ddstring[-1]
        if ending in ['N', 'E', 'S', 'W']:
            keepd[id] = ddstring
            ddstring = ddstring[:-1]
        try:
            dec = dms_dd(*map(float, ddstring.split()))
            if ending in ['S', 'W']:
                dec = -abs(dec)
        except ValueError:
            self.mbox("Check entry " + id, "Calculations STOP")
            return False
        le.setText(f'{dec:0.4f}')
        return True

    def do_calc(self) -> None:
        keepd.clear()
        keepd['GeoCalc'] = GVERSION
        keepd['When'] = strftime("%m-%d %H:%M", localtime())
        radius_model(self.cbxEllipse.currentText())
        if not self.parse_entry(self.enterFromLat, 'FLat'):
            return
        if not self.parse_entry(self.enterFromLon, 'FLon'):
            return
        from_loc = Location(self.enterFromLat.text(),
                            self.enterFromLon.text())

        if not self.parse_entry(self.enterToLat, 'TLat'):
            return
        if not self.parse_entry(self.enterToLon, 'TLon'):
            return
        to_loc = Location(self.enterToLat.text(),
                          self.enterToLon.text())
        keepd["From"] = self.enterFromLocation.text()
        keepd["To"] = self.enterToLocation.text()
        keepd['FromLat'] = self.enterFromLat.text()
        keepd['FromLon'] = self.enterFromLon.text()
        keepd['ToLat'] = self.enterToLat.text()
        keepd['ToLon'] = self.enterToLon.text()

        rpath: GeoPath = rhumb(from_loc, to_loc)
        keepd['r.dist'] = rpath.distance
        keepd['r.bear'] = rpath.course

        gcpath: GeoPath = greatcircle(from_loc, to_loc)
        keepd['gc.dist'] = gcpath.distance
        keepd['gc.course'] = gcpath.course

        self.rhumbDistance.setText(rpath.distance)
        self.rhumbBearing.setText(rpath.course)
        self.gcDistance.setText(gcpath.distance)
        self.gcBearing.setText(gcpath.course)

    def mbox(self, my_message: str, info: str = ""):
        '''
        Bare messagebox with text, info text and OK buttpn
        Concerns:
            MAC OS does not allow window title
            QMessageBox(self) will center over main window,
            --- but (ugly) style will be inherited from parent
        '''
        msg = QMessageBox()
        # msg.setIcon(QMessageBox.Information) # set icon
        msg.setText(my_message)
        msg.setInformativeText(info)
        msg.setStandardButtons(QMessageBox.Ok)
        return_value = msg.exec_()   # execute and catch return
        return return_value

    def do_save(self):
        f = self.enterFromLocation.text()
        t = self.enterToLocation.text()
        # split into pieces to avoid long string...dumb
        logname = f'{f}2{t}.log'
        with open(logname, 'w') as f:
            for key, value in keepd.items():
                f.write(f'{key}: {value}\n')

    # def save_widgets(self):
    #     '''
    #     stub for saving the complete widget list for mainLayout
    #     see vars(self) in Window init
    #     '''
    #     with open("widgets.txt", 'w') as f:
    #         f.write('GeoCalc widget dictionary\n')
    #         for key, value in self.widget_dict.items():
    #             f.write(f'{key} : {value}\n')

    # UI ends here -----------------------------------------------


def dms_dd(degrees: float, minutes: float = 0, seconds: float = 0) -> float:
    if degrees >= 0:
        decimal = degrees + minutes/60.0 + seconds/3600.0
    else:
        decimal = degrees - minutes/60.0 - seconds/3600.0
    return decimal


def main():
    app = QApplication(sys.argv)
    window = Window()
    # print(window.width())   # Used to actual window size
    # print(window.height())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
