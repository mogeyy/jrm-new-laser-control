from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QPainter, QBrush, QPen, QMouseEvent, QFont

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


class CalibrationOverlay(QWidget):
    """
    Semi-transparent overlay drawn on top of inner_circle during calibration.
    Shows 8 numbered target dots; highlights the currently expected one.
    """
    DOT_RADIUS = 8
    FONT_SIZE  = 10

    def __init__(self, parent, target_positions):
        """
        parent           : the inner_circle widget (overlay covers it exactly)
        target_positions : list of 8 (x, y) positions in inner_circle local coords
        """
        super().__init__(parent)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)
        # Also enable mouse tracking on parent so events bubble through
        parent.setMouseTracking(True)

        self.target_positions  = target_positions
        self.current_index     = 0
        self.clicked_points    = []
        self.current_mouse_pos = (parent.width() / 2, parent.height() / 2)

    def mouseMoveEvent(self, event):
        self.current_mouse_pos = (event.position().x(), event.position().y())
        event.accept()

    # ── drawing ───────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dim background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))

        font = QFont()
        font.setPointSize(self.FONT_SIZE)
        font.setBold(True)
        painter.setFont(font)

        r = self.DOT_RADIUS

        for i, (x, y) in enumerate(self.target_positions):
            if i < self.current_index:
                # Already clicked — green
                color = QColor(0, 200, 80)
                label_color = QColor(255, 255, 255)
            elif i == self.current_index:
                # Current target — bright yellow, pulsing border
                color = QColor(255, 220, 0)
                label_color = QColor(0, 0, 0)
            else:
                # Future — grey
                color = QColor(180, 180, 180, 160)
                label_color = QColor(60, 60, 60)

            # Dot fill
            painter.setBrush(QBrush(color))
            # White ring around active target for visibility
            if i == self.current_index:
                painter.setPen(QPen(QColor(255, 255, 255), 2))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(x - r), int(y - r), r * 2, r * 2)

            # Number label
            painter.setPen(QPen(label_color))
            painter.drawText(int(x - r), int(y - r), r * 2, r * 2,
                             Qt.AlignmentFlag.AlignCenter, str(i + 1))

        # Instruction text at top
        painter.setPen(QPen(QColor(255, 255, 255)))
        font2 = QFont()
        font2.setPointSize(9)
        painter.setFont(font2)
        remaining = len(self.target_positions) - self.current_index
        if remaining > 0:
            msg = f"Calibration: point your laser at target {self.current_index + 1} and click it"
        else:
            msg = "All points captured! Calibration complete."
        painter.drawText(self.rect().adjusted(4, 4, -4, -4),
                         Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                         msg)

    # ── interaction ───────────────────────────────────────────────────────────
    def register_current_position(self):
        """Confirm the current mouse position as the calibration point for this target."""
        if self.current_index >= len(self.target_positions):
            return False   # already done

        self.clicked_points.append(self.current_mouse_pos)
        print(f"  Registered point {self.current_index + 1}: {self.current_mouse_pos}")
        self.current_index += 1
        self.update()      # repaint

        if self.current_index >= len(self.target_positions):
            return True    # signal: all done
        return False

    @property
    def is_complete(self):
        return self.current_index >= len(self.target_positions)


class PreviewWindow(QWidget):
    """
    Standalone moveable window showing the calibration-warped dot position.
    The circle boundary is always a plain circle — only the dot is warped.
    """
    DOT_RADIUS = 5

    def __init__(self, diameter: int):
        super().__init__()
        self.setWindowTitle("Galvo Preview (Calibrated)")
        self._margin = 20
        self._inset  = 10
        total = diameter + self._margin * 2
        self.setFixedSize(total, total)
        self._diameter = diameter
        self._radius   = diameter / 2
        self.dot_x = self._radius
        self.dot_y = self._radius

    def set_dot(self, local_x: float, local_y: float):
        from calibration import calibration_map
        wx, wy = calibration_map.apply(local_x, local_y)
        self.dot_x = wx
        self.dot_y = wy
        self.update()

    def paintEvent(self, event):
        import math
        from calibration import calibration_map

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        m   = self._margin
        d   = self._diameter
        ins = self._inset

        # Plain background
        bg = self.palette().color(QPalette.ColorRole.Window)
        painter.fillRect(self.rect(), bg)

        # Outer black ring
        painter.setBrush(QBrush(QColor("black")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(m, m, d, d)

        # Inner circle background
        painter.setBrush(QBrush(bg))
        painter.drawEllipse(m + ins, m + ins, d - 2*ins, d - 2*ins)

        # Dot — clamped to inner circle boundary
        cx = self._radius
        cy = self._radius
        dx = self.dot_x - cx
        dy = self.dot_y - cy
        dist = math.sqrt(dx**2 + dy**2)
        inner_r = self._radius - ins
        if dist > inner_r and dist > 0:
            scale = inner_r / dist
            px = cx + dx * scale
            py = cy + dy * scale
        else:
            px, py = self.dot_x, self.dot_y

        r = self.DOT_RADIUS
        painter.setBrush(QBrush(QColor("red")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(m + px - r), int(m + py - r), r*2, r*2)

        # Status label
        status = "calibrated output" if calibration_map.is_fitted else "uncalibrated"
        painter.setPen(QPen(QColor(120, 120, 120)))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(4, 4, -4, -4),
                         Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                         status)
