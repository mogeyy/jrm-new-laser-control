from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QPainter, QBrush, QPen, QMouseEvent

class Square(QWidget):
    # square = self.Square(window, x position, y position, width, height)
    def __init__(self, parent, x, y, width, height, color='black'):
        super().__init__(parent)
        self.setGeometry(x, y, width, height)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

class Circle(QWidget):
    def __init__(self, parent, x, y, width, height, color='red'):
        super().__init__(parent)
        self.setGeometry(x, y, width, height)
        self.color = QColor(color)
        self.setAutoFillBackground(False) # We will handle painting ourselves

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.color, Qt.BrushStyle.SolidPattern))
        painter.setPen(Qt.PenStyle.NoPen) # No border
        painter.drawEllipse(self.rect())