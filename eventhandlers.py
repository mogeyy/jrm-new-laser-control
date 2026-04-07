from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt
import numpy as np
from constants import w, h, border, capped_speed, max_cursor_speed
from calibration import get_target_positions, N_POINTS, calibration_map

class MainWindowLogic:

    '''============
    SLIDER CONTROLS
    ============'''

    # Line Velocity Slider Control
    def line_velocity_slider_value_changed(self, value):
        self.line_velocity_label.setText(f"{value}")
        self.line_velocity = value

    # Circle Radius Slider Control
    def circle_radius_slider_value_changed(self, value):
        self.circle_radius_label.setText(f"{value}")
        self.circle_radius = value

    # Circle Velocity Slider Control
    def circle_velocity_slider_value_changed(self, value):
        self.circle_velocity_label.setText(f"{value}")
        self.circle_velocity = value

    # User updates the max value of the slider through the input field
    def update_slider_max(self):
        try:
            max_value = int(self.line_velocity_input.text())
            self.line_velocity_slider.setMaximum(max_value)
            print(f"Slider max value updated to: {max_value}")
        except ValueError:
            print("Invalid input for slider max value. Please enter an integer.")

    def circle_mode_clockwise_button_clicked(self):
        self.circle_mode_clockwise = not self.circle_mode_clockwise
        print(f"Circle mode clockwise set to: {self.circle_mode_clockwise}")

    '''================
    LASER POINT CONTROL
    ================'''

    def _update_preview(self, local_x: float, local_y: float):
        """Push raw laser position to the preview window, which applies the warp."""
        if hasattr(self, 'preview_window') and self.preview_window is not None:
            self.preview_window.set_dot(local_x, local_y)

    def _send_to_daq(self, local_x: float, local_y: float):
        """
        Convert calibrated pixel coords to voltages and send to the DAQ.
        Pixel (0,0) -> min_volt, pixel (diameter,diameter) -> max_volt, linear.
        """
        if not (hasattr(self, 'daq') and self.daq is not None):
            return
        from calibration import calibration_map
        cal_x, cal_y = calibration_map.apply(local_x, local_y)
        diameter = float(self.inner_circle.width())
        min_v = self.daq.min_volt
        max_v = self.daq.max_volt
        volt_x = min_v + (cal_x / diameter) * (max_v - min_v)
        volt_y = min_v + (cal_y / diameter) * (max_v - min_v)
        self.daq.set_position(volt_x, volt_y)
        self.daq_x = volt_x
        self.daq_y = volt_y


    def update_game(self):
        # Current mouse position
        mouse_x, mouse_y = self.cursor_position
        radius = self.inner_circle.width() / 2
        center_x = radius
        center_y = radius


        '''=================
        CURSOR MODE (DEFAULT)
        ================='''

        if self.current_mode == "Calibration Mode":
            # Track cursor using calibration_map instead of inner_circle
            mouse_x, mouse_y = self.cursor_position
            # Map the mouse position using calibration_map
            cal_x, cal_y = calibration_map.apply(mouse_x, mouse_y)
            # Use the same speed logic as Cursor Mode
            prev_x, prev_y = self.laser_point_position
            dx = cal_x - prev_x
            dy = cal_y - prev_y
            dist_to_target = np.sqrt(dx**2 + dy**2)
            move_x, move_y = cal_x, cal_y
            global_x = int(self.inner_circle.x() + move_x - self.laser_point.width() / 2)
            global_y = int(self.inner_circle.y() + move_y - self.laser_point.height() / 2)
            self.laser_point.move(global_x, global_y)
            self.laser_point_position = (move_x, move_y)
            self._update_preview(move_x, move_y)
            self._send_to_daq(move_x, move_y)
        if self.current_mode == "Cursor Mode":
            dist_mouse_from_center = np.sqrt((mouse_x - center_x)**2 + (mouse_y - center_y)**2)

            if dist_mouse_from_center <= radius:
                self.active_target = (mouse_x, mouse_y)

            if not hasattr(self, 'active_target'):
                self.active_target = self.laser_point_position

            target_x, target_y = self.active_target
            prev_x, prev_y = self.laser_point_position

            dx = target_x - prev_x
            dy = target_y - prev_y
            dist_to_target = np.sqrt(dx**2 + dy**2)

            if self.capped_speed and dist_to_target > self.max_cursor_speed:
                move_x = prev_x + (dx / dist_to_target) * self.max_cursor_speed
                move_y = prev_y + (dy / dist_to_target) * self.max_cursor_speed
            else:
                move_x, move_y = target_x, target_y

            global_x = int(self.inner_circle.x() + move_x - self.laser_point.width() / 2)
            global_y = int(self.inner_circle.y() + move_y - self.laser_point.height() / 2)

            self.laser_point.move(global_x, global_y)
            self.laser_point_position = (move_x, move_y)
            self._update_preview(move_x, move_y)
            self._send_to_daq(move_x, move_y)

            '''======
            LINE MODE
            ======'''

        elif self.current_mode == "Line Mode":
            if self.line_mode_capturing and self.line_mode_path:
                target_x, target_y = self.line_mode_path[self.line_mode_current_index]
                prev_x, prev_y = self.laser_point_position

                dx = target_x - prev_x
                dy = target_y - prev_y
                dist_to_target = np.sqrt(dx**2 + dy**2)

                if dist_to_target > self.max_cursor_speed:
                    move_x = prev_x + (dx / dist_to_target) * self.line_velocity/10
                    move_y = prev_y + (dy / dist_to_target) * self.line_velocity/10
                else:
                    move_x, move_y = target_x, target_y
                    self.line_mode_current_index += 1
                    if self.line_mode_current_index >= len(self.line_mode_path):
                        self.line_mode_capturing = False

                global_x = int(self.inner_circle.x() + move_x - self.laser_point.width() / 2)
                global_y = int(self.inner_circle.y() + move_y - self.laser_point.height() / 2)
                self.laser_point.move(global_x, global_y)
                self.laser_point_position = (move_x, move_y)
                self._update_preview(move_x, move_y)
                self._send_to_daq(move_x, move_y)

            '''========
            CIRCLE MODE
            ========'''

        elif self.current_mode == "Circle Mode":
            rotation_rate = self.circle_velocity
            self.current_angle += rotation_rate if self.circle_mode_clockwise else -rotation_rate
            r = self.circle_radius
            move_x = int(mouse_x - border + center_x + r * np.cos(np.radians(self.current_angle)) - self.laser_point.width() / 2)
            move_y = int(mouse_y + 2*border + 0*center_y + r * np.sin(np.radians(self.current_angle)) - self.laser_point.height() / 2)

            self.laser_point.move(move_x, move_y)
            self._update_preview(move_x, move_y)
            self._send_to_daq(move_x, move_y)

        self.current_voltages.setText(f"({self.daq_x:.2f}, {self.daq_y:.2f})")

    
    '''=============================
    LEFT CLICK AND KEYBOARD HANDLERS
    ============================='''

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            click_x, click_y = event.position().x(), event.position().y()
            print(f"Mouse clicked at: ({click_x}, {click_y})")

            # ── Line Mode click handling ───────────────────────────────────
            if self.current_mode == "Line Mode" and not self.line_mode_capturing:
                geometry = self.inner_circle.geometry()
                center_x = geometry.x() + geometry.width() / 2
                center_y = geometry.y() + geometry.height() / 2
                radius = geometry.width() / 2
                dist_from_center = np.sqrt((click_x - center_x)**2 + (click_y - center_y)**2)
                if dist_from_center <= radius:
                    rel_x = click_x - geometry.x()
                    rel_y = click_y - geometry.y()
                    self.line_mode_path.append((rel_x, rel_y))
                    print(f"Captured point for Line Mode: ({rel_x}, {rel_y})")
                else:
                    print("Click was outside the circle. Point not captured.")

    def keyPressEvent(self, event):
        print(self.current_mode)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # ── Calibration: Enter confirms current laser position ─────────
            if self.current_mode == "Calibration Mode":
                if hasattr(self, '_cal_overlay') and self._cal_overlay is not None:
                    from PyQt6.QtGui import QCursor
                    # QCursor.pos() always works regardless of focus/event routing
                    global_pos = QCursor.pos()
                    local_pos  = self.inner_circle.mapFromGlobal(global_pos)
                    self._cal_overlay.current_mouse_pos = (float(local_pos.x()), float(local_pos.y()))
                    print(f"  Enter pressed, cursor at inner_circle local: ({local_pos.x():.1f}, {local_pos.y():.1f})")
                    done = self._cal_overlay.register_current_position()
                    if done:
                        self._finish_calibration()
                return

            if self.current_mode == "Line Mode":
                if not self.line_mode_capturing:
                    print("Starting Line Mode path traversal.")
                    self.line_mode_capturing = True
                    self.line_mode_current_index = 0
                else:
                    print("Line Mode path traversal already in progress.")
            else:
                print("No points captured for Line Mode or not in Line Mode.")

    '''=============================
    LASER DOT MOTION CONTROL FOR GUI
    ============================='''


    def laser_point_mouse_move(self, event: QMouseEvent):
        self.cursor_position = (event.position().x(), event.position().y())

    '''=============================
    CALIBRATION MODE IMPLEMENTATION
    ============================='''

    def on_calibration_mode_clicked(self):
        """Enter calibration mode: show the overlay and wait for 8 Enter presses."""
        from PyQt6.QtWidgets import QApplication
        from objects import CalibrationOverlay

        print("Calibration Mode activated! Point your laser at each numbered target and click it.")
        self.current_mode = "Calibration Mode"

        # Hide all slider panels
        for widget in [self.line_velocity_slider, self.line_velocity_label,
                       self.line_velocity_input, self.line_velocity_title,
                       self.circle_radius_slider, self.circle_radius_label,
                       self.circle_radius_input, self.circle_radius_title,
                       self.circle_velocity_slider, self.circle_velocity_label,
                       self.circle_velocity_input, self.circle_velocity_title]:
            widget.setVisible(False)

        # Reset any previous calibration overlay
        if hasattr(self, '_cal_overlay') and self._cal_overlay is not None:
            self._cal_overlay.deleteLater()
            self._cal_overlay = None

        # Build the 8 target positions on the inner circle
        ic = self.inner_circle
        cx = ic.width()  / 2
        cy = ic.height() / 2
        ring_radius = cx * 0.95   # 75 % of the inner circle radius

        self._cal_target_positions = get_target_positions(cx, cy, ring_radius)
        self._cal_real_positions   = self._cal_target_positions   # ideal = target

        # Create and show the overlay on top of inner_circle
        self._cal_overlay = CalibrationOverlay(ic, self._cal_target_positions)
        self._cal_overlay.raise_()
        self._cal_overlay.show()

    def _finish_calibration(self):
        """Called once all 8 clicks have been registered."""
        screen_pts = self._cal_overlay.clicked_points   # what user clicked
        real_pts   = self._cal_real_positions           # ideal target positions

        calibration_map.fit(screen_pts, real_pts)
        print("Calibration complete! Warp map fitted.")
        print(f"  Screen points : {screen_pts}")
        print(f"  Real points   : {real_pts}")

        # Remove overlay and return to Cursor Mode
        self._cal_overlay.hide()
        self._cal_overlay.deleteLater()
        self._cal_overlay = None

        self.current_mode = "Cursor Mode"
        # Re-hide mode-specific panels (cursor mode shows none)
        for widget in [self.line_velocity_slider, self.line_velocity_label,
                       self.line_velocity_input, self.line_velocity_title,
                       self.circle_radius_slider, self.circle_radius_label,
                       self.circle_radius_input, self.circle_radius_title,
                       self.circle_velocity_slider, self.circle_velocity_label,
                       self.circle_velocity_input, self.circle_velocity_title]:
            widget.setVisible(False)

    def calibration_mode(self):
        """Alias kept for compatibility."""
        self.on_calibration_mode_clicked()

    '''==========
    MODE HANDLERS
    =========='''

    def on_cursor_mode_clicked(self):
        self.current_mode = "Cursor Mode"
        print("Cursor Mode activated!")
        for i in [self.line_velocity_slider,
                    self.line_velocity_label,
                    self.line_velocity_input,
                    self.line_velocity_title,
                    self.circle_radius_slider,
                    self.circle_radius_label,
                    self.circle_radius_input,
                    self.circle_radius_title,
                    self.circle_velocity_slider,
                    self.circle_velocity_label,
                    self.circle_velocity_input,
                    self.circle_velocity_title]:
            i.setVisible(False)

    def on_circle_mode_clicked(self):
        print("Circle Mode activated!")
        self.current_mode = "Circle Mode"
        for i in [self.line_velocity_slider,
                    self.line_velocity_label,
                    self.line_velocity_input,
                    self.line_velocity_title]:
            i.setVisible(False)
        for i in [self.circle_radius_slider,
                    self.circle_radius_label,
                    self.circle_radius_input,
                    self.circle_radius_title,
                    self.circle_velocity_slider,
                    self.circle_velocity_label,
                    self.circle_velocity_input,
                    self.circle_velocity_title]:
            i.setVisible(True)

    def on_line_mode_clicked(self):
        print("Line Mode activated! Click any number of points within the circle, then press enter to begin automated laser movement.")
        self.current_mode = "Line Mode"

        self.line_mode_path = []
        self.line_mode_capturing = False
        self.line_mode_current_index = 0

        for i in [self.circle_radius_slider,
                    self.circle_radius_label,
                    self.circle_radius_input,
                    self.circle_radius_title,
                    self.circle_velocity_slider,
                    self.circle_velocity_label,
                    self.circle_velocity_input,
                    self.circle_velocity_title]:
            i.setVisible(False)
        for i in [self.line_velocity_slider,
                    self.line_velocity_label,
                    self.line_velocity_input,
                    self.line_velocity_title]:
            i.setVisible(True)

    def on_capped_speed_toggled(self):
        self.capped_speed = not self.capped_speed
        print(f"Capped Speed set to: {self.capped_speed}")

    def on_rotate_clockwise_toggled(self):
        self.circle_mode_clockwise = not self.circle_mode_clockwise
        print(f"Circle Mode Rotate Clockwise set to: {self.circle_mode_clockwise}")

    def on_clear_line_mode_path_clicked(self):
        self.line_mode_path = []
        self.line_mode_current_index = 0
        print("Line Mode path cleared!")
