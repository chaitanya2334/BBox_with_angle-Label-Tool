import tkinter as tk
from tkinter.filedialog import askdirectory

from PIL import Image, ImageTk
import shape
import os
import glob
import math as m
import cmath as cm
import numpy as np
import re

# shape options for annotations
SHAPE_TYPES = ['Polygon', 'Circle']
# image sizes for the examples
SIZE = 480, 640
# radius for selecting shapes
SELECT_RADIUS = 12


class LabelTool:
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = tk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=1)
        self.parent.resizable(width=tk.FALSE, height=tk.FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.image_name = ''
        self.label_filename = ''
        self.tkimg = None

        # initialize mouse state
        self.shapeIdList = []
        self.shapeId = None
        self.shapeList = []
        self.shape = None
        self.selected_shape_idx = -1
        self.dragging = False

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.in_label = tk.Label(self.frame, text="Image Dir:")
        self.in_label.grid(row=0, column=0, sticky=tk.E)
        self.in_entry = tk.Entry(self.frame)
        self.in_entry.grid(row=0, column=1, sticky=tk.W + tk.E)
        self.in_ldBtn = tk.Button(self.frame, text="Browse", command=self.load_img_dir)
        self.in_ldBtn.grid(row=0, column=2, sticky=tk.W + tk.E)

        # dir entry & load
        self.out_label = tk.Label(self.frame, text="Label Dir:")
        self.out_label.grid(row=1, column=0, sticky=tk.E)
        self.out_entry = tk.Entry(self.frame)
        self.out_entry.grid(row=1, column=1, sticky=tk.W + tk.E)
        self.out_ldBtn = tk.Button(self.frame, text="Browse", command=self.load_out_dir)
        self.out_ldBtn.grid(row=1, column=2, sticky=tk.W + tk.E)

        # main panel for labeling
        self.mainPanel = tk.Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("z", lambda event: self.mainPanel.focus_set())
        self.mainPanel.bind("<Button-1>", self.mouse_click)
        self.mainPanel.bind("<ButtonRelease-1>", self.mouse_release)
        self.mainPanel.bind("<Motion>", self.mouse_move)
        self.parent.bind_all("<Escape>", self.cancel_shape)  # press <Espace> to cancel current bbox
        self.parent.bind("<Delete>", self.del_shape)  # press <Delete> to cancel the selection
        self.parent.bind("a", self.prev_image)  # press <up> to go backforward
        self.parent.bind("d", self.next_image)  # press <down> to go forward

        # self.parent.bind("<Home>",self.loadDir)        # press <Enter> to load dir
        self.mainPanel.grid(row=2, column=1, rowspan=4, sticky=tk.W + tk.N)

        # showing shape info & delete bbox
        self.lb1 = tk.Label(self.frame, text='Bounding Shapes:')
        self.lb1.grid(row=2, column=2, sticky=tk.W + tk.N)
        self.listbox = tk.Listbox(self.frame, width=38, height=12)
        self.listbox.grid(row=3, column=2, sticky=tk.N)
        self.btnDel = tk.Button(self.frame, text='Delete', command=self.del_shape)
        self.btnDel.grid(row=4, column=2, sticky=tk.W + tk.E + tk.N)
        self.btnClear = tk.Button(self.frame, text='ClearAll', command=self.clear_shape)
        self.btnClear.grid(row=5, column=2, sticky=tk.W + tk.E + tk.N)

        # toggling between shape types
        self.shape_type_label = tk.Label(self.frame, text='Shape Type:          ')
        self.shape_type_label.grid(row=3, column=0, sticky=tk.W + tk.S)
        self.shape_type = tk.StringVar(self.frame)
        self.shape_type.set('Select Shape Type')
        self.shape_type_menu = tk.OptionMenu(self.frame, self.shape_type, *SHAPE_TYPES)
        self.shape_type_menu.grid(row=4, column=0, sticky=tk.W + tk.N)

        # control panel for image navigation
        self.ctrPanel = tk.Frame(self.frame)
        self.ctrPanel.grid(row=6, column=1, columnspan=2, sticky=tk.W + tk.E)
        self.prevBtn = tk.Button(self.ctrPanel, text='<< Prev', width=10, command=self.prev_image)
        self.prevBtn.pack(side=tk.LEFT, padx=5, pady=3)
        self.nextBtn = tk.Button(self.ctrPanel, text='Next >>', width=10, command=self.next_image)
        self.nextBtn.pack(side=tk.LEFT, padx=5, pady=3)
        self.progLabel = tk.Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=tk.LEFT, padx=5)
        self.tmpLabel = tk.Label(self.ctrPanel, text="Go to Image filename")
        self.tmpLabel.pack(side=tk.LEFT, padx=5)
        self.idxEntry = tk.Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=tk.LEFT)
        self.idxEntry.bind('<FocusOut>', lambda e: self.idxEntry.select_clear())
        self.goBtn = tk.Button(self.ctrPanel, text='Go', command=self.goto_image)
        self.goBtn.pack(side=tk.LEFT)

        # display mouse position
        self.disp = tk.Label(self.ctrPanel, text='')
        self.disp.pack(side=tk.RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

        print('initialized label tool')


    def load_img_dir(self, dbg=False):
        if not dbg:

            tk.Tk().withdraw()
            s = askdirectory()
            self.in_entry.insert(0, s)
            s = self.in_entry.get()
            self.parent.focus()
            self.category = str(s)
        else:
            s = r'D:\workspace\python\labelGUI'

        # get image list
        self.imageDir = s

        def atoi(text):
            return int(text) if text.isdigit() else text

        def natural_keys(text):
            return [atoi(c) for c in re.split('(\d+)', text)]

        self.imageList = glob.glob(os.path.join(self.imageDir, '*.png'))
        self.imageList.extend(glob.glob(os.path.join(self.imageDir, '*.jpg')))
        self.imageList.sort(key=natural_keys)
        if len(self.imageList) == 0:
            print('No .png images found in the specified dir!')
            return
        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)
        print('%d images loaded from %s' % (self.total, s))

    def load_out_dir(self, dbg=False):
        if not dbg:
            tk.Tk().withdraw()
            s = askdirectory()
            self.out_entry.insert(0, s)
            s = self.out_entry.get()
            self.parent.focus()
            self.outDir = str(s)
        else:
            s = r'D:\workspace\python\labelGUI'
        # set up output dir
        print("label file loading from this dir: {0}".format(self.outDir))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.load_image()

    # # get the rectangle's four corners
    # def get_rect(self, x0, y0, x1, y1, x2, y2):
    #
    #     w = m.sqrt(((x0 - x1) ** 2) + ((y0 - y1) ** 2))
    #     h = m.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))
    #     m1 = self.slope(x1, y1, x2, y2)
    #     m2 = self.slope(x0, y0, x1, y1)
    #     if m1 == np.inf:
    #         x3 = x0
    #     elif m2 == np.inf:
    #         x3 = x2
    #     else:
    #         x3 = ((y0 - m1 * x0) - (y2 - m2 * x2)) / -(m1 - m2)
    #
    #     if m1 == np.inf:
    #         y3 = m2 * x3 + (y2 - m2 * x2)
    #     else:
    #         y3 = m1 * x3 + (y0 - m1 * x0)
    #     corner_x = (x0 / 2, x1 / 2, x2 / 2, int(x3 / 2))
    #     corner_y = (y0 / 2, y1 / 2, y2 / 2, int(y3 / 2))
    #     return tuple(zip(corner_x, corner_y)), w, h

    def load_image(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        img = Image.open(imagepath)
        width, height = img.size
        img = img.resize((int(width / 2), int(height / 2)), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(img)
        self.mainPanel.config(width=max(self.tkimg.width(), 100), height=max(self.tkimg.height(), 100))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=tk.NW)
        self.progLabel.config(text="{0}/{1}".format(os.path.basename(self.imageList[self.cur - 1]),
                                                    os.path.basename(self.imageList[self.total - 1])))

        # load labels
        self.clear_shape()
        self.image_name = os.path.split(imagepath)[-1].split('.')[0]
        label_name = self.image_name + '.txt'
        print("label directory:" + self.outDir)
        self.label_filename = os.path.join(self.outDir, label_name)
        print("label save path:" + self.label_filename)
        if os.path.exists(self.label_filename):
            with open(self.label_filename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        continue
                    split = line.split(' ')
                    parsable = " ".join(split[1:])
                    shape_type = split[0]
                    if shape_type == 'POLY':
                        tmp = shape.Polygon(parse=parsable)
                    elif shape_type == 'CIRC':
                        tmp = shape.Circle(parse=parsable)
                    else:
                        raise RuntimeError("unknown shape: " + shape_type)

                    self.shapeList.append(tmp)

                    tmp_id = self.draw_shape(tmp, idx=i-1)
                    self.shapeIdList.append(tmp_id)
                    self.listbox.insert(tk.END, str(i - 1) + ': ' + tmp.to_string())

    def save_image(self):
        print("saving image in:" + self.label_filename)
        with open(self.label_filename, 'w') as f:
            f.write('%d\n' % len(self.shapeList))
            for shp in self.shapeList:
                # f.write(' '.join(map(str, shp)) + '\n')
                f.write(shp.to_parsable() + '\n')
        print('Image No. %d saved' % self.cur)

    def draw_shape(self, shape, idx=-1, mouse_loc=None, width=2, color='cyan', selected=False, location=None):
        id = []
        old_loc = shape.location
        if location:
            shape.set_center(location)
        if idx != -1:
            id.extend(self.create_extras(idx, shape.get_font_size(idx), selected, shape.location))
        id.extend(shape.create_shape(self.mainPanel, mouse_loc, width, color))
        if old_loc:
            shape.set_center(old_loc)
        return id

    def create_extras(self, idx, font_size, selected, location):
        extras = []
        extras.append(self.mainPanel.create_text(location[0], location[1], font=('Ariel', font_size + 3), text=str(idx), fill = 'black'))
        extras.append(self.mainPanel.create_text(location[0], location[1], font=('Ariel', font_size), text=str(idx), fill = 'yellow'))
        if selected:
            extras.append(self.mainPanel.create_oval(location[0] - SELECT_RADIUS,
                                                     location[1] - SELECT_RADIUS,
                                                     location[0] + SELECT_RADIUS,
                                                     location[1] + SELECT_RADIUS,
                                                     fill='',
                                                     outline='blue',
                                                     width=2))
        return extras

    def mouse_click(self, event):

        if self.shape:
            self.shape.handle_click([event.x, event.y])
            if self.shape.defined:
                self.del_shape_id(self.shapeId)
                self.listbox.insert(tk.END, str(len(self.shapeList)) + ': ' + self.shape.to_string())
                self.shapeIdList.append(self.draw_shape(self.shape, idx=len(self.shapeList)))
                self.shapeList.append(self.shape)
                self.shapeId = None
                self.shape = None
                self.save_image()
        else:
            closest_idx = -1
            closest_dist = m.inf
            for i, shp in enumerate(self.shapeList):
                dist = shape.Shape.dist(shp.location[0], shp.location[1], event.x, event.y)
                if dist < closest_dist:
                    closest_idx = i
                    closest_dist = dist
            if closest_dist <= SELECT_RADIUS and closest_idx != self.selected_shape_idx:
                self.dragging = True
                if self.selected_shape_idx != -1:
                    self.listbox.selection_clear(0, tk.END)
                    self.del_shape_id(self.shapeIdList[self.selected_shape_idx])
                    self.shapeIdList[self.selected_shape_idx] = self.draw_shape(self.shapeList[self.selected_shape_idx], idx=self.selected_shape_idx)
                self.selected_shape_idx = closest_idx
                self.listbox.selection_set(self.selected_shape_idx)
                self.del_shape_id(self.shapeIdList[self.selected_shape_idx])
                self.shapeIdList[self.selected_shape_idx] = self.draw_shape(self.shapeList[self.selected_shape_idx], idx=self.selected_shape_idx, selected=True, color='red')
            elif closest_dist <= SELECT_RADIUS and closest_idx == self.selected_shape_idx:
                self.listbox.selection_clear(0, tk.END)
                self.del_shape_id(self.shapeIdList[self.selected_shape_idx])
                self.shapeIdList[self.selected_shape_idx] = self.draw_shape(self.shapeList[self.selected_shape_idx], idx=self.selected_shape_idx)
                self.selected_shape_idx = -1
            else:
                if self.shape_type.get() != 'Select Shape Type':
                    new_shape_opts = {'Polygon': shape.Polygon(),
                                      'Circle': shape.Circle()}
                    self.shape = new_shape_opts[self.shape_type.get()]
                    self.shape.handle_click([event.x, event.y])

    def mouse_release(self, event):
        if self.selected_shape_idx != -1 and self.dragging:
            self.dragging = False
            self.shapeList[self.selected_shape_idx].set_center([event.x, event.y])
            self.del_shape_id(self.shapeIdList[self.selected_shape_idx])
            self.shapeIdList[self.selected_shape_idx] = self.draw_shape(self.shapeList[self.selected_shape_idx], idx=self.selected_shape_idx, selected=True)
            self.listbox.delete(self.selected_shape_idx)
            self.listbox.insert(self.selected_shape_idx, str(self.selected_shape_idx) + ': ' + self.shapeList[self.selected_shape_idx].to_string())
            self.listbox.selection_set(self.selected_shape_idx)
            self.save_image()

    def mouse_move(self, event):
        self.disp.config(text='x: %d, y: %d' % (event.x, event.y))

        if self.shape:
            if self.shapeId:
                self.del_shape_id(self.shapeId)
            self.shapeId = self.draw_shape(self.shape, mouse_loc=[event.x, event.y])
        else:
            if self.selected_shape_idx != -1 and self.dragging:
                self.del_shape_id(self.shapeIdList[self.selected_shape_idx])
                self.shapeList[self.selected_shape_idx].set_center([event.x, event.y])
                self.shapeIdList[self.selected_shape_idx] = self.draw_shape(self.shapeList[self.selected_shape_idx], idx=self.selected_shape_idx, mouse_loc=[event.x, event.y], color='red', selected=True)
            closest_idx = -1
            closest_dist = m.inf
            closest_outside_idx = -1
            closest_outside_dist = m.inf
            for i, shp in enumerate(self.shapeList):
                dist = shape.Shape.dist(shp.location[0], shp.location[1], event.x, event.y)
                if dist < closest_dist:
                    closest_idx = i
                    closest_dist = dist
                if SELECT_RADIUS < dist < closest_outside_dist:
                    closest_outside_idx = i
                    closest_outside_dist = dist
            if closest_dist <= SELECT_RADIUS and closest_idx != self.selected_shape_idx:
                self.del_shape_id(self.shapeIdList[closest_idx])
                self.shapeIdList[closest_idx] = self.draw_shape(self.shapeList[closest_idx], idx=closest_idx, color='red', width=2)
            if closest_outside_idx != -1:
                self.del_shape_id(self.shapeIdList[closest_outside_idx])
                self.shapeIdList[closest_outside_idx] = self.draw_shape(self.shapeList[closest_outside_idx], idx=closest_outside_idx, selected=self.selected_shape_idx==closest_outside_idx)

    def del_shape_id(self, shape_id):
        if shape_id:
            for shp in shape_id:
                self.mainPanel.delete(shp)

    def cancel_shape(self):
        if self.shapeId:
            self.del_shape_id(self.shapeId)
            self.shapeId = None
            self.shape = None

    def del_shape(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        if idx == self.selected_shape_idx:
            self.selected_shape_idx = -1
        self.del_shape_id(self.shapeIdList[idx])
        self.shapeIdList.pop(idx)
        self.shapeList.pop(idx)
        self.listbox.delete(0, tk.END)
        for i, shp in enumerate(self.shapeList):
            shp.index = i
            self.del_shape_id(self.shapeIdList[i])
            self.shapeIdList[i] = self.draw_shape(shp, idx=i)
            self.listbox.insert(tk.END, str(i) + ': ' + shp.to_string())
        self.save_image()

    def clear_shape(self):
        for idx in range(len(self.shapeIdList)):
            self.del_shape_id(self.shapeIdList[idx])
        self.listbox.delete(0, len(self.shapeList))
        self.shapeIdList = []
        self.shapeList = []
        if self.label_filename:
            self.save_image()

    def prev_image(self, event=None):
        self.save_image()
        if self.cur > 1:
            self.cur -= 1
            self.load_image()

    def next_image(self, event=None):
        self.save_image()
        if self.cur < self.total:
            self.cur += 1
            self.load_image()

    def goto_image(self):
        filename = self.idxEntry.get()
        print(self.imageList[0])
        if any(filename in s for s in self.imageList):
            self.save_image()
            self.cur = [i for i, s in enumerate(self.imageList) if filename in s][0] + 1
            self.load_image()
            self.parent.focus()
