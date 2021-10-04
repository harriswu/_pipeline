from dev.package.ui.qt import *

import math


class NodeGraphicsScene(QGraphicsScene):
    """
    scene's graphic object, handle how scene (background) should visually behave in the viewport
    """
    def __init__(self, scene, parent=None):
        super(NodeGraphicsScene, self).__init__(parent)
        # store scene object for easier access later
        self.scene = scene

        # background settings
        self._subdivisions = 35
        self._grid = 5

        self._color_background = QColor('#393939')
        self._color_subdivisions = QColor('#2f2f2f')
        self._color_grid = QColor('#292929')

        self._pen_subdivisions = QPen(self._color_subdivisions)
        self._pen_subdivisions.setWidth(1)
        self._pen_grid = QPen(self._color_grid)
        self._pen_grid.setWidth(2)

        self.setBackgroundBrush(self._color_background)

    @property
    def subdivisions(self):
        """
        get background's subdivisions
        """
        return self._subdivisions

    @property
    def grid(self):
        """
        get background's grid
        """
        return self._grid

    @property
    def color_subdivisions(self):
        """
        get subdivisions color
        """
        return self._color_subdivisions

    @property
    def color_grid(self):
        """
        get grid color
        """
        return self._color_grid

    def set_gr_scene(self, width, height):
        """
        set graphic scene to fit in the scene object, this function will be called in scene object level

        Args:
            width (float): scene's width
            height (float): scene's height
        """
        self.setSceneRect(-width // 2, -height // 2, width, height)

    def drawBackground(self, painter, rect):
        """
        draw background subdivisions and grids
        """
        super(NodeGraphicsScene, self).drawBackground(painter, rect)
        # create grid
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - left % self._subdivisions
        first_top = top - top % self._subdivisions

        # compute all lines
        grid_size = self._subdivisions * self._grid
        lines_subdivisions, lines_grid = [], []
        for x in range(first_left, right, self._subdivisions):
            if x % grid_size:
                lines_subdivisions.append(QLine(x, top, x, bottom))
            else:
                lines_grid.append(QLine(x, top, x, bottom))

        for y in range(first_top, bottom, self._subdivisions):
            if y % grid_size:
                lines_subdivisions.append(QLine(left, y, right, y))
            else:
                lines_grid.append(QLine(left, y, right, y))

        # draw the lines
        painter.setPen(self._pen_subdivisions)
        painter.drawLines(lines_subdivisions)

        painter.setPen(self._pen_grid)
        painter.drawLines(lines_grid)
