import tkinter as tk
from PIL import Image, ImageTk
import os
import glob
import math as m
import cmath as cm
import numpy as np

# colors for the bounding boxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 480, 640


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
        self.STATE = {'click': 0, 'x': 0, 'y': 0, 'gR': [], 'gR_deg': 0}
        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = tk.Label(self.frame, text="Image Dir:")
        self.label.grid(row=0, column=0, sticky=tk.E)
        self.entry = tk.Entry(self.frame)
        self.entry.grid(row=0, column=1, sticky=tk.W + tk.E)
        self.ldBtn = tk.Button(self.frame, text="Load", command=self.load_dir)
        self.ldBtn.grid(row=0, column=2, sticky=tk.W + tk.E)

        # main panel for labeling
        self.mainPanel = tk.Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouse_click)
        self.mainPanel.bind("<Motion>", self.mouse_move)
        self.parent.bind("<Escape>", self.cancel_bbox)  # press <Espace> to cancel current bbox
        self.parent.bind("<Delete>", self.del_bbox)  # press <Delete> to cancel the selection
        self.parent.bind("<Prior>", self.prev_image)  # press <up> to go backforward
        self.parent.bind("<Next>", self.next_image)  # press <down> to go forward
        # self.parent.bind("<Home>",self.loadDir)        # press <Enter> to load dir
        self.mainPanel.grid(row=1, column=1, rowspan=4, sticky=tk.W + tk.N)

        # showing bbox info & delete bbox
        self.lb1 = tk.Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=1, column=2, sticky=tk.W + tk.N)
        self.listbox = tk.Listbox(self.frame, width=28, height=12)
        self.listbox.grid(row=2, column=2, sticky=tk.N)
        self.btnDel = tk.Button(self.frame, text='Delete', command=self.del_bbox)
        self.btnDel.grid(row=3, column=2, sticky=tk.W + tk.E + tk.N)
        self.btnClear = tk.Button(self.frame, text='ClearAll', command=self.clear_bbox)
        self.btnClear.grid(row=4, column=2, sticky=tk.W + tk.E + tk.N)

        # control panel for image navigation
        self.ctrPanel = tk.Frame(self.frame)
        self.ctrPanel.grid(row=5, column=1, columnspan=2, sticky=tk.W + tk.E)
        self.prevBtn = tk.Button(self.ctrPanel, text='<< Prev', width=10, command=self.prev_image)
        self.prevBtn.pack(side=tk.LEFT, padx=5, pady=3)
        self.nextBtn = tk.Button(self.ctrPanel, text='Next >>', width=10, command=self.next_image)
        self.nextBtn.pack(side=tk.LEFT, padx=5, pady=3)
        self.progLabel = tk.Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=tk.LEFT, padx=5)
        self.tmpLabel = tk.Label(self.ctrPanel, text="Go to Image No.")
        self.tmpLabel.pack(side=tk.LEFT, padx=5)
        self.idxEntry = tk.Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=tk.LEFT)
        self.goBtn = tk.Button(self.ctrPanel, text='Go', command=self.goto_image)
        self.goBtn.pack(side=tk.LEFT)

        # example pannel for illustration
        self.egPanel = tk.Frame(self.frame, border=10)
        self.egPanel.grid(row=1, column=0, rowspan=5, sticky=tk.N)
        self.tmpLabel2 = tk.Label(self.egPanel, text="")
        self.tmpLabel2.pack(side=tk.TOP, pady=5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(tk.Label(self.egPanel))
            self.egLabels[-1].pack(side=tk.TOP)

        # display mouse position
        self.disp = tk.Label(self.ctrPanel, text='')
        self.disp.pack(side=tk.RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

    def load_dir(self, dbg=False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = str(s)
        else:
            s = r'D:\workspace\python\labelGUI'

        # get image list
        self.imageDir = os.path.join(r'./Images', self.category)
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.png'))
        if len(self.imageList) == 0:
            print('No .png images found in the specified dir!')
            return
        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = os.path.join(r'./Labels', self.category)
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        self.load_image()
        print('%d images loaded from %s' % (self.total, s))

    # get the rectangle's four corners
    def get_rect(self, x0, y0, x1, y1, x2, y2):
        w = m.sqrt(((x0 - x1) ** 2) + ((y0 - y1) ** 2))
        h = m.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        m1 = self.slope(x1, y1, x2, y2)
        m2 = self.slope(x0, y0, x1, y1)

        x3 = ((y0 - m1 * x0) - (y2 - m2 * x2)) / -(m1 - m2)
        y3 = m1 * x3 + (y0 - m1 * x0)
        corner_x = x0, x1, x2, x3
        corner_y = y0, y1, y2, y3
        return tuple(zip(corner_x, corner_y)), w, h

    def load_image(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(img)
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=tk.NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clear_bbox()
        self.image_name = os.path.split(imagepath)[-1].split('.')[0]
        label_name = self.image_name + '.txt'
        self.label_filename = os.path.join(self.outDir, label_name)
        bbox_cnt = 0
        if os.path.exists(self.label_filename):
            with open(self.label_filename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    tmp = [float(t.strip()) for t in line.split()]
                    # print tmp
                    self.bboxList.append(tuple(tmp))
                    xc, yc = tmp[0], tmp[1]
                    x0, y0 = xc + tmp[2] / 2, yc + tmp[3] / 2
                    poly_tmp = list(self.get_rect_corner(xc, yc, x0, y0))
                    tmp_id = self.mainPanel.create_polygon(poly_tmp[0],
                                                           width=2,
                                                           outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)],
                                                           fill='')
                    angle = cm.exp(m.radians(tmp[4]) * 1j)
                    offset = complex(xc, yc)
                    new_xy = []
                    for x, y in poly_tmp[0]:
                        v = angle * (complex(x, y) - offset) + offset
                        new_xy.append(v.real)
                        new_xy.append(v.imag)
                    # print np.angle(angle,deg=True)
                    self.mainPanel.coords(tmp_id, *new_xy)

                    self.bboxIdList.append(tmp_id)
                    self.listbox.insert(tk.END,
                                        '(%d, %d), w:%d, h:%d, deg:%.2f' % (tmp[0], tmp[1], tmp[2], tmp[3], tmp[4]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                            fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def save_image(self):
        with open(self.label_filename, 'w') as f:
            f.write('%d\n' % len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print('Image No. %d saved' % self.cur)

    def slope(self, x0, y0, x1, y1):
        dx = x1 - x0
        dy = y1 - y0
        try:
            return dy / dx
        except ZeroDivisionError:
            return 0.0  # cannot determine angle

    def mouse_click(self, event):
        # print "click state:{}".format(self.STATE['click'])

        if self.STATE['click'] == 0:
            self.STATE['x0'], self.STATE['y0'] = event.x, event.y

        elif self.STATE['click'] == 1:
            self.STATE['x1'], self.STATE['y1'] = event.x, event.y

        elif self.STATE['click'] == 2:
            x0, x1, x2 = self.STATE['x0'], self.STATE['x1'], event.x
            y0, y1, y2 = self.STATE['y0'], self.STATE['y1'], event.y
            self.STATE['gR'] = list(self.get_rect(x0, y0, x1, y1, x2, y2))
            # print "Rectangle corner:",self.STATE['gR'][0]
            self.bboxList.append(
                (self.STATE['x'], self.STATE['y'], self.STATE['gR'][1], self.STATE['gR'][2], self.STATE['gR_deg']))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(tk.END, '(%d, %d), w:%d, h:%d, deg:%.2f' % (self.STATE['x'], self.STATE['y'],
                                                                            self.STATE['gR'][1], self.STATE['gR'][2],
                                                                            self.STATE['gR_deg']))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
            self.STATE['click'] = -1

        self.STATE['click'] += 1

    def mouse_move(self, event):
        self.disp.config(text='x: %d, y: %d' % (event.x, event.y))
        if self.tkimg:  # mouse tracking
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)

        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            x0, x1 = self.STATE['x0'], event.x
            y0, y1 = self.STATE['y0'], event.y

            # print self.STATE['gR']
            self.bboxId = self.mainPanel.create_line(x0, y0, x1, y1, width=2,
                                                     fill=COLORS[len(self.bboxList) % len(COLORS)])

        if 2 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)

            x0, x1, x2 = self.STATE['x0'], self.STATE['x1'], event.x
            y0, y1, y2 = self.STATE['y0'], self.STATE['y1'], event.y
            global start
            angle = np.rad2deg(np.arctan2(y1 - y0, x1 - x0))
            self.STATE['gR'] = list(self.get_rect(x0, y0, x1, y1, x2, y2))
            self.bboxId = self.mainPanel.create_polygon(self.STATE['gR'][0],
                                                        width=2,
                                                        outline=COLORS[len(self.bboxList) % len(COLORS)],
                                                        fill='')
            # print np.angle(angle,deg=True)
            self.STATE['gR_deg'] = np.angle(angle, deg=True)


    def cancel_bbox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = -1

    def del_bbox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)
        self.STATE['click'] = 0

    def clear_bbox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
        self.STATE['click'] = 0

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
        idx = int(self.idxEntry.get())
        if 1 <= idx <= self.total:
            self.save_image()
            self.cur = idx
            self.load_image()
