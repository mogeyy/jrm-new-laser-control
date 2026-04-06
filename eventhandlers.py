from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt
import numpy as np
from constants import w, h, border, capped_speed, max_cursor_speed

class MainWindowLogic:

    '''============
    SLIDER CONTROLS
    ============'''

    # Line Velocity Slider Control
    def line_velocity_slider_value_changed(self, value):
        self.line_velocity_label.setText(f"{value}")
        self.line_velocity = value
        # print(f"Slider value changed to: {value}")

    # Circle Radius Slider Control
    def circle_radius_slider_value_changed(self, value):
        self.circle_radius_label.setText(f"{value}")
        self.circle_radius = value
        # print(f"Slider value changed to: {value}")

    # Circle Velocity Slider Control
    def circle_velocity_slider_value_changed(self, value):
        self.circle_velocity_label.setText(f"{value}")
        self.circle_velocity = value
        # print(f"Slider value changed to: {value}")

    # User updates the max value of the slider through the input field
    def update_slider_max(self):
        try:
            max_value = int(self.line_velocity_input.text())
            self.line_velocity_slider.setMaximum(max_value)
            # self.line_velocity_slider_label.setText(f"{max_value}")
            print(f"Slider max value updated to: {max_value}")
        except ValueError:
            print("Invalid input for slider max value. Please enter an integer.")

    def circle_mode_clockwise_button_clicked(self):
        self.circle_mode_clockwise = not self.circle_mode_clockwise
        print(f"Circle mode clockwise set to: {self.circle_mode_clockwise}")

    '''================
    LASER POINT CONTROL
    ================='''

    def update_game(self):
        # Current mouse position
        mouse_x, mouse_y = self.cursor_position
        radius = self.inner_circle.width() / 2
        center_x = radius
        center_y = radius

        '''=================
        CURSOR MODE (DEFAULT)
        ================='''

        if self.current_mode == "Cursor Mode":
        # check distance between cursor and center of target circle
            dist_mouse_from_center = np.sqrt((mouse_x - center_x)**2 + (mouse_y - center_y)**2)
        
            # If mouse is outside, self.active_target stays at the last valid coordinate
            if dist_mouse_from_center <= radius:
                self.active_target = (mouse_x, mouse_y)
            
            # Ensure active_target exists (initialization safety)
            if not hasattr(self, 'active_target'):
                self.active_target = self.laser_point_position

            # Calculate movement vector toward active target
            target_x, target_y = self.active_target
            prev_x, prev_y = self.laser_point_position

            dx = target_x - prev_x
            dy = target_y - prev_y
            dist_to_target = np.sqrt(dx**2 + dy**2)

            if self.capped_speed and dist_to_target > self.max_cursor_speed:
                # Move at max speed toward the last valid inside position
                move_x = prev_x + (dx / dist_to_target) * self.max_cursor_speed
                move_y = prev_y + (dy / dist_to_target) * self.max_cursor_speed
            else:
                # If we are close or uncapped, just arrive
                move_x, move_y = target_x, target_y

            # Move the laser point
            global_x = int(self.inner_circle.x() + move_x - self.laser_point.width() / 2)
            global_y = int(self.inner_circle.y() + move_y - self.laser_point.height() / 2)
            
            self.laser_point.move(global_x, global_y)
            self.laser_point_position = (move_x, move_y)

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

            '''========
            CIRCLE MODE
            ========'''

        elif self.current_mode == "Circle Mode":
            rotation_rate = self.circle_velocity # per second
            self.current_angle += rotation_rate if self.circle_mode_clockwise else -rotation_rate #* (1/60) # assuming update_game is called 60 times per second
            radius = self.circle_radius
            move_x = int(mouse_x - border + center_x + radius * np.cos(np.radians(self.current_angle)) - self.laser_point.width() / 2)
            move_y = int(mouse_y + 2*border + 0*center_y + radius * np.sin(np.radians(self.current_angle)) - self.laser_point.height() / 2)
            self.laser_point.move(move_x, move_y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            click_x, click_y = event.position().x(), event.position().y()
            print(f"Mouse clicked at: ({click_x}, {click_y})")
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
            if self.current_mode == "Line Mode":# and self.line_mode_path:
                if not self.line_mode_capturing:
                    print("Starting Line Mode path traversal.")
                    self.line_mode_capturing = True
                    self.line_mode_current_index = 0
                else:
                    print("Line Mode path traversal already in progress.")
            else:
                print("No points captured for Line Mode or not in Line Mode.")

    def laser_point_mouse_move(self, event: QMouseEvent):
        self.cursor_position = (event.position().x(), event.position().y())

    '''=========
    MODE HANDLER - hides or shows UI elements based on which mode is selected
    ========='''
    
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