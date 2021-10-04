from dev.package.ui.qt import *


class GraphicsEdge(QGraphicsPathItem):
    """
    node's graphic edge, handle how edge should visually behave in viewport
    """
    def __init__(self, edge, parent=None):
        super(GraphicsEdge, self).__init__(parent)

        # store node edge class for easier access later
        self.edge = edge

        # visual preset
        self._color = QColor('#001000')
        self._color_selected = QColor('#00ff00')
        self._color_dragging = QColor('#eeff00')
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._color_selected)
        self._pen_dragging = QPen(self._color_dragging)
        self._pen_dragging.setStyle(Qt.DashLine)
        self._pen.setWidthF(2.0)
        self._pen_selected.setWidthF(2.0)
        self._pen_dragging.setWidthF(2.0)

        # make edge selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        # put edge under socket
        self.setZValue(-1)

        # give start/end position a default value
        self._pos_source = [0, 0]
        self._pos_target = [200, 100]

    @property
    def pos_source(self):
        """
        start point's position
        """
        return self._pos_source

    @pos_source.setter
    def pos_source(self, value):
        """
        set start point's position

        Args:
            value (list): start point's x and z values
        """
        self._pos_source = value

    @property
    def pos_target(self):
        """
        end point's position
        """
        return self._pos_target

    @pos_target.setter
    def pos_target(self, value):
        """
        set end point's position

        Args:
            value (list): end point's x and z values
        """
        self._pos_target = value

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        """
        paint edge in viewport
        """
        self.setPath(self.get_path())
        if not self.edge.end_socket:
            # dragging the edge around while mouse is moving
            painter.setPen(self._pen_dragging)
        else:
            # connect two points with edge
            painter.setPen(self._pen if not self.isSelected() else self._pen_selected)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

    def get_path(self):
        """
        will handle drawing QPainterPath from point A to B
        """
        raise NotImplementedError('This method has to be overridden in a child class')

    def intersect_with(self, p1, p2):
        """
        check if current path is intersect with the line from given two points

        Args:
            p1 (QPointF): start point
            p2 (QPointF): end point

        Returns:
            True/False
        """
        cut_path = QPainterPath(p1)
        cut_path.lineTo(p2)
        return cut_path.intersects(self.path())

    def update(self, *args, **kwargs):
        super(GraphicsEdge, self).update(*args, **kwargs)


class GraphicsEdgeDirect(GraphicsEdge):
    def get_path(self):
        """
        get edge path using straight line drawing method
        """
        path = QPainterPath(QPointF(self.pos_source[0], self.pos_source[1]))
        path.lineTo(self.pos_target[0], self.pos_target[1])
        return path


class GraphicsEdgeBezier(GraphicsEdge):
    def get_path(self):
        """
        get edge path using bezier drawing method
        """
        distance = abs(self.pos_target[0] - self.pos_source[0]) * 0.5

        path = QPainterPath(QPointF(self.pos_source[0], self.pos_source[1]))

        if self.edge.start_socket.socket_type == self.edge.start_socket.INPUT_SOCKET:
            ctrl_pnts = [self.pos_source[0] - distance, self.pos_target[0] + distance]
        else:
            ctrl_pnts = [self.pos_source[0] + distance, self.pos_target[0] - distance]

        path.cubicTo(ctrl_pnts[0], self.pos_source[1], ctrl_pnts[1], self.pos_target[1], self.pos_target[0],
                     self.pos_target[1])
        return path
