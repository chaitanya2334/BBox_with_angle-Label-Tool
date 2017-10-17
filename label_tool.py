import tkinter as tk
from tkinter.filedialog import askdirectory

from PIL import Image, ImageTk
import os
import glob
import math as m
import cmath as cm
import numpy as np
import re

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
        self.mainPanel.bind("<Button-1>", self.mouse_click)
        self.mainPanel.bind("<Motion>", self.mouse_move)
        self.parent.bind("<Escape>", self.cancel_bbox)  # press <Espace> to cancel current bbox
        self.parent.bind("<Delete>", self.del_bbox)  # press <Delete> to cancel the selection
        self.parent.bind("<Prior>", self.prev_image)  # press <up> to go backforward
        self.parent.bind("<Next>", self.next_image)  # press <down> to go forward
        # self.parent.bind("<Home>",self.loadDir)        # press <Enter> to load dir
        self.mainPanel.grid(row=2, column=1, rowspan=4, sticky=tk.W + tk.N)

        # showing bbox info & delete bbox
        self.lb1 = tk.Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=2, column=2, sticky=tk.W + tk.N)
        self.listbox = tk.Listbox(self.frame, width=38, height=12)
        self.listbox.grid(row=3, column=2, sticky=tk.N)
        self.btnDel = tk.Button(self.frame, text='Delete', command=self.del_bbox)
        self.btnDel.grid(row=4, column=2, sticky=tk.W + tk.E + tk.N)
        self.btnClear = tk.Button(self.frame, text='ClearAll', command=self.clear_bbox)
        self.btnClear.grid(row=5, column=2, sticky=tk.W + tk.E + tk.N)

        # control panel for image navigation
        self.ctrPanel = tk.Frame(self.frame)
        self.ctrPanel.grid(row=6, column=1, columnspan=2, sticky=tk.W + tk.E)
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
        self.egPanel.grid(row=2, column=0, rowspan=5, sticky=tk.N)
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



    # get the rectangle's four corners
    def get_rect(self, x0, y0, x1, y1, x2, y2):

        w = m.sqrt(((x0 - x1) ** 2) + ((y0 - y1) ** 2))
        h = m.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))
        m1 = self.slope(x1, y1, x2, y2)
        m2 = self.slope(x0, y0, x1, y1)
        if m1 == np.inf:
            x3 = x0
        elif m2 == np.inf:
            x3 = x2
        else:
            x3 = ((y0 - m1 * x0) - (y2 - m2 * x2)) / -(m1 - m2)

        if m1 == np.inf:
            y3 = m2 * x3 + (y2 - m2 * x2)
        else:
            y3 = m1 * x3 + (y0 - m1 * x0)
        print(m1)
        print(m2)
        corner_x = (x0 / 2, x1 / 2, x2 / 2, int(x3 / 2))
        corner_y = (y0 / 2, y1 / 2, y2 / 2, int(y3 / 2))
        return tuple(zip(corner_x, corner_y)), w, h

    def load_image(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        img = Image.open(imagepath)
        width, height = img.size
        img = img.resize((int(width / 2), int(height / 2)), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(img)
        self.mainPanel.config(width=max(self.tkimg.width(), 100), height=max(self.tkimg.height(), 100))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=tk.NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clear_bbox()
        self.image_name = os.path.split(imagepath)[-1].split('.')[0]
        label_name = self.image_name + '.txt'
        print(self.outDir)
        self.label_filename = os.path.join(self.outDir, label_name)
        print(self.label_filename)
        bbox_cnt = 0
        if os.path.exists(self.label_filename):
            with open(self.label_filename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    tmp = [float(t.strip()) for t in line.split()]
                    print(tmp)
                    # print tmp
                    self.bboxList.append(tuple(tmp))

                    poly_tmp = list(tmp)
                    tmp_id = self.mainPanel.create_polygon(poly_tmp,
                                                           width=2,
                                                           outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)],
                                                           fill='')
                    # print np.angle(angle,deg=True)
                    self.bboxIdList.append(tmp_id)
                    self.listbox.insert(tk.END,
                                        '({}, {}),({}, {}),({}, {}),({}, {})'.format(*tmp))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                            fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def save_image(self):
        print(self.label_filename)
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
            return np.inf  # cannot determine angle

    def mouse_click(self, event):
        # print "click state:{}".format(self.STATE['click'])

        if self.STATE['click'] == 0:
            self.STATE['x0'], self.STATE['y0'] = event.x, event.y

        elif self.STATE['click'] == 1:
            self.STATE['x1'], self.STATE['y1'] = event.x, event.y

        elif self.STATE['click'] == 2:
            x0, x1, x2 = self.STATE['x0'], self.STATE['x1'], event.x
            y0, y1, y2 = self.STATE['y0'], self.STATE['y1'], event.y
            self.STATE['gR'] = list(self.get_rect(2 * x0, 2 * y0, 2 * x1, 2 * y1, 2 * x2, 2 * y2))
            # print "Rectangle corner:",self.STATE['gR'][0]
            self.bboxList.append(
                [int(element) for tupl in self.STATE['gR'][0] for element in tupl])
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            print(self.STATE['gR'])
            self.listbox.insert(tk.END, '({}, {}),({}, {}),({}, {}),({}, {})'.format(
                *[int(element) for tupl in self.STATE['gR'][0] for element in tupl]))
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
            self.STATE['gR'] = list(self.get_rect(2 * x0, 2 * y0, 2 * x1, 2 * y1, 2 * x2, 2 * y2))
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
