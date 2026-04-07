import numpy as np
from scipy.interpolate import RBFInterpolator

# ── Calibration configuration ─────────────────────────────────────────────────
# The 8 physical targets are evenly spaced on a ring.
# expressed as unit offsets from the circle centre (–1..1).
# Angle 0 = right, going clockwise.
N_POINTS = 8
ANGLES_DEG = [i * 360 / N_POINTS for i in range(N_POINTS)]   # 0,45,90,...,315

def get_target_positions(center_x, center_y, ring_radius):
    """
    Return the 8 on-screen overlay positions (pixels, relative to inner_circle)
    that correspond to the physical calibration ring.
    """
    positions = []
    for deg in ANGLES_DEG:
        rad = np.radians(deg)
        x = center_x + ring_radius * np.cos(rad)
        y = center_y + ring_radius * np.sin(rad)
        positions.append((x, y))
    return positions          # list of 8 (x, y) tuples


class CalibrationMap:
    """
    Stores the correspondence between:
      - 'real' points  : the known physical positions (our 8 unit-circle targets)
      - 'screen' points: where the user actually clicked for each target

    After fitting, apply() warps any raw screen coordinate into the corrected
    'real-world-aligned' coordinate.
    """

    def __init__(self):
        self._rbf_x = None   # RBFInterpolator: screen → corrected x
        self._rbf_y = None
        self.is_fitted = False
        self.screen_points = []   # what the user clicked  (N×2)
        self.real_points   = []   # known target positions (N×2)

    def fit(self, screen_points, real_points):
        """
        screen_points : list of (sx, sy) – where user clicked
        real_points   : list of (rx, ry) – the corresponding ideal positions
        Both lists must be length N_POINTS.
        """
        sp = np.array(screen_points, dtype=float)   # (8,2)
        rp = np.array(real_points,   dtype=float)   # (8,2)

        self.screen_points = screen_points
        self.real_points   = real_points

        # Thin-plate-spline RBF (kernel='thin_plate_spline') generalises well
        # with a small number of landmarks.
        # Check if all points are identical (mouse tracking failed)
        if len(set(screen_points)) == 1:
            raise ValueError("All calibration points are identical — mouse tracking failed. "
                             "Move the mouse to each target before pressing Enter.")

        # Use linear kernel with smoothing — robust with 8 sparse points
        self._rbf_x = RBFInterpolator(rp, sp[:, 0], kernel='linear', smoothing=0.0)
        self._rbf_y = RBFInterpolator(rp, sp[:, 1], kernel='linear', smoothing=0.0)
        self.is_fitted = True

    def apply(self, x, y):
        """
        Given a raw screen position (x, y) return the calibration-corrected
        position.  If the map is not fitted yet, returns (x, y) unchanged.
        """
        if not self.is_fitted:
            return x, y
        pt = np.array([[x, y]], dtype=float)
        cx = float(self._rbf_x(pt)[0])
        cy = float(self._rbf_y(pt)[0])
        return cx, cy

    def reset(self):
        self._rbf_x = None
        self._rbf_y = None
        self.is_fitted = False
        self.screen_points = []
        self.real_points   = []


# Module-level singleton used by the rest of the app
calibration_map = CalibrationMap()
