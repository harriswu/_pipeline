from dev.package.ui.qt import *

    
class GraphicsSocket(QGraphicsItem):
    """
    node's graphic socket, handle how socket should visually behave in viewport
    """
    def __init__(self, socket):
        super(GraphicsSocket, self).__init__(socket.node.gr_node)
        # store socket object for easier access later
        self.socket = socket

        # visual settings
        self._radius = 6.0
        self._outline_width = 1.0
        self._color = QColor('#FFFF7700')
        self._color_outline = QColor('FF000000')

        self._pen = QPen(self._color_outline)
        self._pen.setWidth(self._outline_width)
        self._brush = QBrush(self._color)

    @property
    def radius(self):
        """
        get socket's radius
        """
        return self._radius

    @property
    def outline_width(self):
        """
        get socket outline's width
        """
        return self._outline_width

    @property
    def color(self):
        """
        get socket color
        """
        return self._color

    @property
    def color_outline(self):
        """
        get socket outline color
        """
        return self._color_outline

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        """
        paint the socket
        """
        # painting circle
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(-self._radius, -self._radius, 2 * self._radius, 2 * self._radius)

    def boundingRect(self):
        """
        defines the outer bounds of the item as a rectangle
        """
        return QRectF(-self._radius - self._outline_width, -self._radius - self._outline_width,
                      2 * (self._radius + self._outline_width), 2 * (self._radius + self._outline_width))
