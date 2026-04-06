from PyQt6.QtWidgets import (QLineEdit, QMainWindow, QPushButton, QLabel, QSlider)
from PyQt6.QtCore import Qt
from constants import w, h, border

class UIButton(QPushButton):
    def __init__(
             self
            ,text:          str = ""
            ,width:         int = int(w - h - 2*border)
            ,height:        int = int(h/12)
            ,parent:        QMainWindow = None
            ,on_startup:    bool = False
    ):
        super().__init__(text, parent)
        self.setFixedSize(width, height)
        self.setStyleSheet("font-size: 16px;")
        self.setVisible(on_startup)

class UIToggle(QPushButton):
    def __init__(
             self
            ,text:          str = ""
            ,width:         int = int(w - h - 2*border)
            ,height:        int = int(h/12)
            ,parent:        QMainWindow = None
            ,on_startup:    bool = False
    ):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedSize(width, height)
        self.setStyleSheet("font-size: 16px;")
        self.setVisible(on_startup)

class UILabel(QLabel):
    def __init__(
             self 
            ,text :         str = ""
            ,x_pos :        int = 0  
            ,y_pos :        int = 0 
            ,parent:        QMainWindow = None
            ,on_startup:    bool = False
    ):
        super().__init__(text, parent)
        self.setStyleSheet(f"font-size: 14px;")
        self.setGeometry(x_pos, y_pos, 100, 20)
        self.setVisible(on_startup)

class UIInput(QLineEdit):
    def __init__(
             self
            ,placeholder:   int = 0         
            ,x_pos:         int = 0
            ,y_pos:         int = 0
            ,width:         int = int(w - h - 2*border)
            ,height:        int = 20
            ,parent:        QMainWindow = None
            ,on_startup:    bool = False
        ):

        super().__init__(parent)
        self.setGeometry(x_pos, y_pos, width, height)
        self.setPlaceholderText(str(placeholder))
        self.setStyleSheet("font-size: 14px;")
        self.setVisible(on_startup)

class UISlider(QSlider):
    def __init__(
             self
            ,x_pos:             int = 0 
            ,y_pos:             int = 0
            ,width:             int = w - h - 2 * border
            ,initial_value:     int = 0
            ,max_value:         int = 100
            ,parent:            QMainWindow = None
            ,orientation:       Qt.Orientation = Qt.Orientation.Horizontal
            ,on_startup:        bool = False
        ):
        super().__init__(orientation, parent)
        self.setMaximum(max_value)
        self.setGeometry(x_pos, y_pos, width, 20)
        self.setVisible(on_startup)
        self.setValue(int(initial_value))

class DefaultSliderSet():
    def __init__(
             self
            ,parent:            QMainWindow = None
            ,title:             str = ""
            ,x_pos:             int = 0
            ,y_pos:             int = 0
            ,slider_width:      int = w - h - 2 * border
            ,slider_max:        int = 100
            ,slider_initial:    int = 0
            ,input_placeholder: int = 100
            ,input_width:       int = int(w - h - 2*border)
            ,input_height:      int = 20
            ,above:             bool = True
            ,on_startup:        bool = False
    ): 
        label_text = str(slider_initial)
        self.slider = UISlider(
             x_pos         = x_pos 
            ,y_pos         = y_pos 
            ,width         = slider_width 
            ,initial_value = slider_initial 
            ,max_value     = slider_max 
            ,parent        = parent 
            ,orientation   = Qt.Orientation.Horizontal 
            ,on_startup    = on_startup
        )

        label_y_pos = y_pos - 20 if above else y_pos + 20
        input_y_pos = label_y_pos

        self.label = UILabel(
             text       = label_text 
            ,x_pos      = x_pos
            ,y_pos      = label_y_pos
            ,parent     = parent
            ,on_startup = on_startup
        )

        self.title = UILabel(
             text       = title
            ,x_pos      = x_pos
            ,y_pos      = label_y_pos - 20
            ,parent     = parent
            ,on_startup = on_startup
        )

        self.input = UIInput(
             placeholder = input_placeholder 
            ,x_pos       = x_pos + slider_width - int(slider_width/5) 
            ,y_pos       = input_y_pos + border*0 
            ,width       = int(slider_width/5) 
            ,height      = input_height
            ,on_startup  = on_startup
            ,parent      = parent
        )