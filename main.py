import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout)
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import QTimer
from constants import w, h, border, max_cursor_speed, capped_speed
from eventhandlers import MainWindowLogic
from daqcontrol import LaserController
from objects import Square, Circle, PreviewWindow
from uielements import UIButton, DefaultSliderSet, UIToggle, UILabel, UIInput

class MainWindow(QMainWindow, MainWindowLogic):
    def __init__(self):
        super().__init__()

        self.w = w
        self.h = h
        self.border = border
        self.max_cursor_speed = max_cursor_speed
        self.cursor_position = (int( w - h + border + int( ( h - 2 * border ) / 2 ) - 5 ), int( h / 2 ))
        self.laser_point_position = (int( w - h + border + int( ( h - 2 * border ) / 2 ) - 5 ), int( h / 2 ))
        self.capped_speed = capped_speed
        self.timer = QTimer()
        self.timer.setInterval(1000 // 60)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(1000 // 60)
        self.current_mode = "Cursor Mode"
        self.current_angle = 0

        self.line_velocity = 50
        self.circle_radius = 50
        self.circle_velocity = 50
        self.circle_mode_clockwise = False

        self.line_mode_path = []
        self.line_mode_capturing = False
        self.line_mode_current_index = 0

        # Calibration overlay handle (None when not active)
        self._cal_overlay = None

        # ── DAQ initialisation ───────────────────────────────────────────
        self.daq = LaserController()


        # ── Preview window (calibrated galvo output) ──────────────────────
        ic_diameter = h - 2 * border - 2 * 10   # mirrors inner_circle size
        self.preview_window = PreviewWindow(ic_diameter)
        self.preview_window.move(w + 20, 0)
        self.preview_window.show()

        self.setWindowTitle("Laser Control Interface")
        self.setFixedSize(w, h)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        square_size = w - h
        self.outer_circle = Circle(central_widget, square_size + border, border, h - 2 * border, h - 2 * border, color="black")
        difference = 10
        self.inner_circle = Circle(central_widget, square_size + border + difference, border + difference,
                                   h - 2 * border - 2 * difference, h - 2 * border - 2 * difference,
                                   color=self.palette().color(QPalette.ColorRole.Window).name())

        '''========================
        PRIMARY BUTTONS UI ELEMENTS
        ========================'''

        grid_container_1 = QWidget(central_widget)
        primary_buttons = QGridLayout(grid_container_1)
        primary_buttons.setContentsMargins(0, 0, 0, 0)
        primary_buttons.setVerticalSpacing(0)

        cursor_mode_button = UIButton(text="Cursor Mode", parent=grid_container_1, on_startup=True)
        primary_buttons.addWidget(cursor_mode_button, 0, 0)
        cursor_mode_button.clicked.connect(self.on_cursor_mode_clicked)

        circle_mode_button = UIButton(text="Circle Mode", parent=grid_container_1, on_startup=True)
        primary_buttons.addWidget(circle_mode_button, 1, 0)
        circle_mode_button.clicked.connect(self.on_circle_mode_clicked)

        line_mode_button = UIButton(text="Line Mode", parent=grid_container_1, on_startup=True)
        primary_buttons.addWidget(line_mode_button, 2, 0)
        line_mode_button.clicked.connect(self.on_line_mode_clicked)

        # ── Calibration Mode button ──────────────────────────────────────────
        calibration_mode_button = UIButton(text="Calibration Mode", parent=grid_container_1, on_startup=True)
        primary_buttons.addWidget(calibration_mode_button, 3, 0)
        calibration_mode_button.clicked.connect(self.on_calibration_mode_clicked)

        grid_container_1.move(border, int(border / 2 + 1))

        '''==========================
        SECONDARY BUTTONS UI ELEMENTS
        ==========================='''

        grid_container_2 = QWidget(central_widget)
        secondary_buttons = QGridLayout(grid_container_2)
        secondary_buttons.setContentsMargins(0, 0, 0, 0)
        secondary_buttons.setVerticalSpacing(0)

        capped_speed_button = UIToggle(text="Capped Speed", parent=grid_container_2, on_startup=True)
        secondary_buttons.addWidget(capped_speed_button, 0, 0)
        capped_speed_button.clicked.connect(self.on_capped_speed_toggled)

        rotate_clockwise_button = UIToggle(text="Rotate Clockwise", parent=grid_container_2, on_startup=True)
        secondary_buttons.addWidget(rotate_clockwise_button, 1, 0)
        rotate_clockwise_button.clicked.connect(self.on_rotate_clockwise_toggled)

        clear_line_mode_path_button = UIButton(text="Clear Line Mode Path", parent=grid_container_2, on_startup=True)
        secondary_buttons.addWidget(clear_line_mode_path_button, 2, 0)
        clear_line_mode_path_button.clicked.connect(self.on_clear_line_mode_path_clicked)

        grid_container_2.move(border, int(h - border - (h / 12) * 3 - border / 2))

        '''========================
        LASER POINT UI ELEMENTS
        ========================'''

        self.laser_point = Circle(
             self
            ,x      = int(w - h + border + int((h - 2 * border) / 2) - 5)
            ,y      = int(h / 2)
            ,width  = 10
            ,height = 10
            ,color  = 'red'
        )
        self.laser_point.setVisible(True)
        self.laser_point.raise_()

        self.inner_circle.setMouseTracking(True)
        self.inner_circle.mouseMoveEvent = self.laser_point_mouse_move

        '''
        =====================
        LINE MODE UI ELEMENTS
        =====================
        '''

        line_velocity_slider_set = DefaultSliderSet(
             parent             = central_widget
            ,title              = "Linear Velocity"
            ,x_pos              = border
            ,y_pos              = h - 30 * border
            ,slider_width       = w - h - 2 * border
            ,slider_max         = 100
            ,slider_initial     = 50
            ,input_placeholder  = 100
            ,above              = True
            ,on_startup         = False
        )

        self.line_velocity_slider = line_velocity_slider_set.slider
        self.line_velocity_label  = line_velocity_slider_set.label
        self.line_velocity_input  = line_velocity_slider_set.input
        self.line_velocity_title  = line_velocity_slider_set.title

        self.line_velocity_slider.valueChanged.connect(self.line_velocity_slider_value_changed)
        self.line_velocity_input.returnPressed.connect(self.update_slider_max)

        '''
        =======================
        CIRCLE MODE UI ELEMENTS
        =======================
        '''

        circle_radius_slider_set = DefaultSliderSet(
             parent             = central_widget
            ,title              = "Radius"
            ,x_pos              = border
            ,y_pos              = h - 30 * border
            ,slider_width       = w - h - 2 * border
            ,slider_max         = 100
            ,slider_initial     = 50
            ,input_placeholder  = 100
            ,above              = True
            ,on_startup         = False
        )

        self.circle_radius_slider = circle_radius_slider_set.slider
        self.circle_radius_label  = circle_radius_slider_set.label
        self.circle_radius_input  = circle_radius_slider_set.input
        self.circle_radius_title  = circle_radius_slider_set.title

        self.circle_radius_slider.valueChanged.connect(self.circle_radius_slider_value_changed)
        self.circle_radius_input.returnPressed.connect(self.update_slider_max)

        circle_velocity_slider_set = DefaultSliderSet(
             parent             = central_widget
            ,title              = "Angular Velocity"
            ,x_pos              = border
            ,y_pos              = h - 36 * border
            ,slider_width       = w - h - 2 * border
            ,slider_max         = 100
            ,slider_initial     = 50
            ,input_placeholder  = 100
            ,above              = True
            ,on_startup         = False
        )

        self.circle_velocity_slider = circle_velocity_slider_set.slider
        self.circle_velocity_label  = circle_velocity_slider_set.label
        self.circle_velocity_input  = circle_velocity_slider_set.input
        self.circle_velocity_title  = circle_velocity_slider_set.title

        self.circle_velocity_slider.valueChanged.connect(self.circle_velocity_slider_value_changed)
        self.circle_velocity_input.returnPressed.connect(self.update_slider_max)


    def closeEvent(self, event):
        """Shut down the DAQ safely when the window is closed."""
        if hasattr(self, 'daq') and self.daq is not None:
            self.daq.close()
        super().closeEvent(event)

'''
==================================================================
THE THING THAT RUNS THE PROGRAM. PLACE NOTHING BELOW THIS SECTION!
==================================================================
'''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
