from tkinter import Canvas
import math as m

class Shape(object):

    # defines a blank shape or parses one from a given string
    def __init__(self, *to_parse):
        self.defined = False
        self.location = None

    # draws the shape on the panel and returns it whether the shape is partial or complete
    def create_shape(self, panel, mouse_loc):
        raise NotImplementedError('subclasses must override get_shape!')

    # adds to or modifies a shape based on click
    def handle_click(self, loc):
        raise NotImplementedError('subclasses must override handle_click!')

    # returns the approximated font size required for the given number in this shape
    def get_approx_diam(self):
        raise NotImplementedError('subclasses must override get_approx_diam!')

    # changes the center of the shape
    def set_center(self, loc):
        raise NotImplementedError('subclasses must override set_center!')

    # returns the string representing this shape
    def to_string(self):
        raise NotImplementedError('subclasses must override to_string!')

    # returns string that can be parsed to this shape
    def to_parsable(self):
        raise NotImplementedError('subclasses must override to_parsable!')

    # returns the approximated font size required for the given number in this shape
    def get_font_size(self, idx):
        approx_diam = self.get_approx_diam()
        # 1 font size for every 2 pixels of diameter
        # goes down by a factor of 2/3 for every new digit
        est = int(1 / 2 * approx_diam * ((2 / 3) ** (len(str(idx)) - 1)))
        if est > 16:
            return 16
        elif est < 4:
            return 4
        else:
            return est


    # returns the distance between two points
    @staticmethod
    def dist(x1, y1, x2, y2):
        return m.sqrt((x1 - x2)*(x1 - x2) + (y1 - y2)*(y1 - y2))


FINISH_RADIUS = 5


class Polygon(Shape):

    def __init__(self, parse=None):
        super().__init__()
        self.points = []
        if parse:
            self.defined = True
            point = []
            for i, val in enumerate(str(parse).split(' ')):
                point.append(int(val))
                if i % 2 == 1:
                    self.points.append(point)
                    point = []
            self.location = self.get_center()

    def create_shape(self, panel, mouse_loc, width=1, color='blue'):
        if not isinstance(panel, Canvas):
            raise RuntimeError('cannot draw to a non-Canvas object: ' + panel)
        if self.defined:
            return [panel.create_polygon(self.points, width=width, outline=color, fill='')]
        else:
            shape = []
            last = None
            for p in self.points:
                if not (last is None):
                    shape.append(panel.create_line(last[0], last[1], p[0], p[1], width=width, fill=color))
                last = p
            if mouse_loc and self.points:
                shape.append(panel.create_line(p[0], p[1], mouse_loc[0], mouse_loc[1], width=width, fill=color))
                if Shape.dist(self.points[0][0], self.points[0][1], mouse_loc[0], mouse_loc[1]) <= FINISH_RADIUS:
                    shape.append(panel.create_oval(self.points[0][0] - FINISH_RADIUS,
                                                   self.points[0][1] - FINISH_RADIUS,
                                                   self.points[0][0] + FINISH_RADIUS,
                                                   self.points[0][1] + FINISH_RADIUS,
                                                   fill='',
                                                   outline='red',
                                                   width=2))
            return shape

    def handle_click(self, loc):
        if not self.defined:
            if 3 <= len(self.points) and Shape.dist(self.points[0][0], self.points[0][1], loc[0], loc[1]) <= FINISH_RADIUS:
                self.location = self.get_center()
                self.defined = True
            else:
                self.points.append(loc)

    def get_center(self):
        new_loc = [0, 0]
        for p in self.points:
            new_loc[0] += p[0]
            new_loc[1] += p[1]
        return [int(a / len(self.points)) for a in new_loc]

    def get_approx_diam(self):
        total_dist = 0
        for p0 in self.points:
            for p1 in self.points:
                if p0 == p1:
                    continue
                total_dist += Shape.dist(p0[0], p0[1], p1[0], p1[1])
        num_points = len(self.points)
        average_dist = 2 * total_dist / (num_points * (num_points - 1))
        approx_diam = average_dist * m.pi / 2
        # this approximation is less accurate for low vertex shapes
        # so we scale it down by (1 - e^(-num_points))
        return approx_diam * (1 - (m.e ** (-num_points/6)))

    def set_center(self, loc):
        for p in self.points:
            p[0] += loc[0] - self.location[0]
            p[1] += loc[1] - self.location[1]
        self.location = loc

    def to_string(self):
        s = 'POLY - points={'
        for p in self.points:
            s += '(' + str(p[0]) + ',' + str(p[1]) + '),'
        s = s[:-1]
        s += '}'
        return s

    def to_parsable(self):
        s = 'POLY'
        for p in self.points:
            s += ' ' + str(p[0]) + ' ' + str(p[1])
        return s


class Circle(Shape):

    def __init__(self, parse=None):
        super().__init__()
        self.start = None
        if parse:
            self.defined = True
            splt = str(parse).split(' ')
            self.location = [int(splt[0]), int(splt[1])]
            self.radius = int(splt[2])

    def create_shape(self, panel, mouse_loc, width=1, color='blue'):
        if not isinstance(panel, Canvas):
            raise RuntimeError('cannot draw to a non-Canvas object: ' + panel)
        if self.defined:
            return [panel.create_oval(self.location[0] - self.radius,
                                               self.location[1] - self.radius,
                                               self.location[0] + self.radius,
                                               self.location[1] + self.radius,
                                               fill='',
                                               outline=color,
                                               width=width),]
        else:
            if mouse_loc and self.start:
                circ = Circle.get_circ(self.start[0], self.start[1], mouse_loc[0], mouse_loc[1])
                return [panel.create_oval(circ[0] - circ[2],
                                               circ[1] - circ[2],
                                               circ[0] + circ[2],
                                               circ[1] + circ[2],
                                               fill='',
                                               outline=color,
                                               width=width),]

    @staticmethod
    def get_circ(x0, y0, x1, y1):
        rad = m.sqrt(((x0 - x1) ** 2) + ((y0 - y1) ** 2)) / 2
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        return [int(center_x), int(center_y), int(rad)]

    def handle_click(self, loc):
        if not self.defined:
            if self.start:
                circ = Circle.get_circ(self.start[0], self.start[1], loc[0], loc[1])
                self.location = [circ[0], circ[1]]
                self.radius = circ[2]
                self.start = None
                self.defined = True
            else:
                self.start = loc

    def get_approx_diam(self):
        return self.radius * 2

    def set_center(self, loc):
        self.location = loc

    def to_string(self):
        return 'CIRC - center=(' + str(self.location[0]) + ',' + str(self.location[1]) + '), radius=' + str(self.radius)

    def to_parsable(self):
        return 'CIRC ' + str(self.location[0]) + ' ' + str(self.location[1]) + ' ' + str(self.radius)