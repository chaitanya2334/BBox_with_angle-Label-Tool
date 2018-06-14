from tkinter import Canvas
import math as m

SELECT_RADIUS = 8


class Shape(object):

    # defines a blank shape or parses one from a given string
    def __init__(self, index, *to_parse):
        self.index = index
        self.selected = False
        self.defined = False
        self.location = None

    # draws the shape on the panel and returns it whether the shape is partial or complete
    def create_shape(self, panel, mouse_loc):
        raise NotImplementedError('subclasses must override get_shape!')

    # adds to or modifies a shape based on click
    def handle_click(self, loc):
        raise NotImplementedError('subclasses must override handle_click!')

    # returns the string representing this shape
    def to_string(self):
        raise NotImplementedError('subclasses must override to_string!')

    # returns string that can be parsed to this shape
    def to_parsable(self):
        raise NotImplementedError('subclasses must override to_parsable!')

    @staticmethod
    def dist(x1, y1, x2, y2):
        return m.sqrt((x1 - x2)*(x1 - x2) + (y1 - y2)*(y1 - y2))


FINISH_RADIUS = 5


class Polygon(Shape):

    def __init__(self, index, parse=None):
        super().__init__(index)
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

    def create_shape(self, panel, mouse_loc):
        shape = []
        if not isinstance(panel, Canvas):
            raise RuntimeError('cannot draw to a non-Canvas object: ' + panel)
        if self.defined:
            if self.selected and mouse_loc:
                shifted_points = [[p[0] - self.location[0] + mouse_loc[0], p[1] - self.location[1] + mouse_loc[1]] for p in self.points]
                shape.append(panel.create_polygon(shifted_points, width=2, outline='black', fill=''))
                shape.append(panel.create_text(mouse_loc[0], mouse_loc[1], font=('Ariel', 12), text=str(self.index)))
                shape.append(panel.create_oval(mouse_loc[0] - SELECT_RADIUS,
                                               mouse_loc[1] - SELECT_RADIUS,
                                               mouse_loc[0] + SELECT_RADIUS,
                                               mouse_loc[1] + SELECT_RADIUS,
                                               fill='',
                                               outline='blue',
                                               width=2))
            elif not self.selected:
                shape.append(panel.create_polygon(self.points, width=2, outline='black', fill=''))
                shape.append(panel.create_text(self.location[0], self.location[1], font=('Ariel', 12), text=str(self.index)))
        else:
            last = None
            for p in self.points:
                if not (last is None):
                    shape.append(panel.create_line(last[0], last[1], p[0], p[1], width=4))
                last = p
            if mouse_loc and self.points:
                shape.append(panel.create_line(p[0], p[1], mouse_loc[0], mouse_loc[1], width=4))
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
        if self.defined:
            if self.selected:
                for p in self.points:
                    p[0] += loc[0] - self.location[0]
                    p[1] += loc[1] - self.location[1]
                self.location = loc
            else:
                raise RuntimeError('handle_click should not have been called')
        else:
            if not self.selected:
                if self.points and \
                        Shape.dist(self.points[0][0], self.points[0][1], loc[0], loc[1]) <= FINISH_RADIUS:
                    self.location = self.get_center()
                    self.defined = True
                else:
                    self.points.append(loc)
            else:
                raise RuntimeError('shape should not be selected if not already defined')

    def get_center(self):
        new_loc = [0, 0]
        for p in self.points:
            new_loc[0] += p[0]
            new_loc[1] += p[1]
        return [int(a / len(self.points)) for a in new_loc]

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

    def __init__(self, index, parse=None):
        super().__init__(index)
        self.start = None
        if parse:
            self.defined = True
            splt = str(parse).split(' ')
            self.location = [int(splt[0]), int(splt[1])]
            self.radius = int(splt[2])

    def create_shape(self, panel, mouse_loc):
        shape = []
        if not isinstance(panel, Canvas):
            raise RuntimeError('cannot draw to a non-Canvas object: ' + panel)
        if self.defined:
            if self.selected and mouse_loc:
                shape.append(panel.create_oval(mouse_loc[0] - self.radius,
                                               mouse_loc[1] - self.radius,
                                               mouse_loc[0] + self.radius,
                                               mouse_loc[1] + self.radius,
                                               fill='',
                                               width=2))
                shape.append(panel.create_text(mouse_loc[0], mouse_loc[1], font=('Ariel', 12), text=str(self.index)))
                shape.append(panel.create_oval(mouse_loc[0] - SELECT_RADIUS,
                                               mouse_loc[1] - SELECT_RADIUS,
                                               mouse_loc[0] + SELECT_RADIUS,
                                               mouse_loc[1] + SELECT_RADIUS,
                                               fill='',
                                               outline='blue',
                                               width=2))
            elif not self.selected:
                shape.append(panel.create_oval(self.location[0] - self.radius,
                                               self.location[1] - self.radius,
                                               self.location[0] + self.radius,
                                               self.location[1] + self.radius,
                                               fill='',
                                               width=2))
                shape.append(panel.create_text(self.location[0], self.location[1], font=('Ariel', 12), text=str(self.index)))
        else:
            if mouse_loc and self.start:
                circ = Circle.get_circ(self.start[0], self.start[1], mouse_loc[0], mouse_loc[1])
                shape.append(panel.create_oval(circ[0] - circ[2],
                                               circ[1] - circ[2],
                                               circ[0] + circ[2],
                                               circ[1] + circ[2],
                                               fill='',
                                               width=4))
        return shape

    @staticmethod
    def get_circ(x0, y0, x1, y1):
        rad = m.sqrt(((x0 - x1) ** 2) + ((y0 - y1) ** 2)) / 2
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        return [int(center_x), int(center_y), int(rad)]

    def handle_click(self, loc):
        if self.defined:
            if self.selected:
                self.location[0] = loc[0]
                self.location[1] = loc[1]
            else:
                raise RuntimeError('handle_click should not have been called')
        else:
            if not self.selected:
                if self.start:
                    circ = Circle.get_circ(self.start[0], self.start[1], loc[0], loc[1])
                    self.location = [circ[0], circ[1]]
                    self.radius = circ[2]
                    self.start = None
                    self.defined = True
                else:
                    self.start = loc
            else:
                raise RuntimeError('shape should not be selected if not already defined')

    def get_center(self):
        new_loc = [0, 0]
        for p in self.points:
            new_loc[0] += p[0]
            new_loc[1] += p[1]
        return [int(a / len(self.points)) for a in new_loc]

    def to_string(self):
        return 'CIRC - center=(' + str(self.location[0]) + ',' + str(self.location[1]) + '), radius=' + str(self.radius)

    def to_parsable(self):
        return 'CIRC ' + str(self.location[0]) + ' ' + str(self.location[1]) + ' ' + str(self.radius)