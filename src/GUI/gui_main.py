from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QColor
from PyQt6.QtCore import *
from PyQt6 import uic, QtGui

from tabs.main_monitor import *

from_class = uic.loadUiType("inventory_management.ui")

# (UI) QDialog -> QTabWidget -> QWidget
class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        

        QWidget 1
        QWidget 2
        
        



# SensorMonitor : [(20, 30), 400 x 400]