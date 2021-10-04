from dev.package.ui.qt import *


class GraphicsCutLine(QGraphicsItem):
    """
    graphic cut line, handle how cut line should visually behave in viewport
    """
    def __init__(self, parent=None):
        super(GraphicsCutLine, self).__init__(parent)
        # store the points cursor travelling on viewport
        self.line_points = []

        # visual settings
        self._pen = QPen(Qt.white)
        self._pen.setWidthF(2.0)
        self._pen.setDashPattern([3, 3])

        # put cut line always on top
        self.setZValue(2)

    def boundingRect(self):
        return QRectF(0, 0, 1, 1)

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._pen)

        poly = QPolygonF(self.line_points)
        painter.drawPolyline(poly)
