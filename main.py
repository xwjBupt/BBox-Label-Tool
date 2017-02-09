#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#-------------------------------------------------------------------------------
from __future__ import division
try:
    # for Python2
    from Tkinter import *   ## notice capitalized T in Tkinter 
except ImportError:
    # for Python3
    from tkinter import *   ## notice lowercase 't' in tkinter here
import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import shutil

# colors for the bboxes
COLORS = ['#FF69B4', '#DDA0DD', '#00FF00', '#008000', '#FFA500', '#DC143C',
          '#C0C0C0', '#FFE4C4', '#32CD32', '#8B008B', '#6495ED', '#8A2BE2', '#EE82EE',
          '#FF00FF', '#006400', '#7FFF00', '#FF00FF', '#0000CD', '#FF8C00', '#FFEFD5',
          '#C71585', '#7CFC00', '#9370DB', '#6A5ACD', '#B0C4DE', '#4169E1', '#ADFF2F',
          '#FF1493', '#DB7093', '#BA55D3', '#C71585', '#9400D3', '#FF6347', '#90EE90',
          '#FFFF00', '#E6E6FA', '#0000FF', '#808000', '#BDB76B', '#FFFFE0', '#808080',
          '#696969', '#40E0D0', '#CD853F', '#008080', '#48D1CC', '#8B4513', '#FFF5EE',
          '#FAF0E6', '#98FB98', '#00FFFF', '#87CEEB', '#00BFFF', '#B0E0E6', '#00FA9A',
          '#F5FFFA', '#F0E68C', '#F5DEB3', '#008B8B', '#8FBC8F', '#FF0000', '#F08080',
          '#66CDAA', '#3CB371', '#2E8B57', '#A52A2A', '#B22222', '#AFEEEE', '#FFF8DC',
          '#DAA520', '#FFFAF0', '#FDF5E6', '#F4A460', '#D2691E', '#FFD700']
# image sizes for the examples
SIZE = 256, 256

class_name = ['insulator', 'hammer', 'tower', 'nest', 'text']


class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("SeqLabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.rel = dict()
        self.relc = dict()
        self.selected_obj = None
        self.write_dir = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # set default entry
        import sys
        if len(sys.argv) == 2:
            self.entry.insert(0, sys.argv[1])

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row=1, column=1, rowspan=7, sticky=W+N)

        # showing object info & delete bbox
        self.lb2 = Label(self.frame, text='Object index:')
        self.lb2.grid(row=1, column=2, sticky=W+N)
        self.listbox2 = Listbox(self.frame, width=22, height=12)
        self.listbox2.grid(row=2, column=2, sticky=N)
        self.btnDe2 = Button(self.frame, text='Add', command=self.addObj)
        self.btnDe2.grid(row=3, column=2, sticky=W + E + N)
        self.btnDe3 = Button(self.frame, text='Delete', command=self.delObj)
        self.btnDe3.grid(row=4, column=2, sticky=W+E+N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=5, column=2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row=6, column=2, sticky = N)
        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=7, column=2, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=8, column=1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width=10, command = self.prevImage)
        self.prevBtn.pack(side=LEFT, padx=5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width=10, command = self.nextImage)
        self.nextBtn.pack(side=LEFT, padx=5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)


    def loadDir(self, dbg=False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.imageDir = s
        else:
            self.imageDir = ''
        if not os.path.isdir(self.imageDir):
           tkMessageBox.showerror("Error!", message="The specified dir doesn't exist!")
           return
        # get image list
        #self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPG'))
        self.imageList.sort()
        if len(self.imageList) == 0:
            print('No .JPG images found in the specified dir')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join('Labels', os.path.split(self.imageDir)[-1])
        if not os.path.exists(self.outDir):
            os.makedirs(self.outDir)

        self.num = 0
        if os.path.exists(os.path.join(self.outDir, '.num.txt')):
            with open(os.path.join(self.outDir, '.num.txt'), 'r') as f:
                self.num = int(f.readline())

        if os.path.exists(os.path.join(self.outDir, '.col.txt')):
            with open(os.path.join(self.outDir, '.col.txt'), 'r') as f:
                for (i, line) in enumerate(f):
                    tmp = [t.strip() for t in line.split(',')]
                    self.relc[int(tmp[0])] = tmp[1]

        self.loadImage()
        print('%d images loaded from %s' % (self.total, self.imageDir))


    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        img = Image.open(imagepath)
        #img = img.resize((img.size[0]*2, img.size[1]*2), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text="%06d/%06d" % (self.cur, self.total))
        self.write_dir = os.path.join(self.outDir, os.path.split(imagepath)[-1].split('.')[0])

        # load labels
        self.clearBBox()
        if os.path.isdir(self.write_dir):
            curr_labels = glob.glob(os.path.join(self.write_dir, '*.txt'))
            if len(curr_labels) > 0:
            	curr_labels.sort()
                self.clearObj()
                for label_name in curr_labels:
                    id_index = int(os.path.split(label_name)[-1].split('.')[0])
                    color = self.relc[id_index]

                    lines = []
                    with open(label_name, 'r') as f:
                        for line in f.readlines():
                            tmp = [int(t.strip()) for t in line.split(',')]
                            tmpId = self.mainPanel.create_rectangle(tmp[0], tmp[1],
                                                                    tmp[2], tmp[3],
                                                                    width=2,
                                                                    outline=color)
                            self.bboxList.append(tuple(tmp))
                            self.bboxIdList.append(tmpId)
                            self.listbox.insert(END, '(%d, %d, %d, %d)' % (tmp[0], tmp[1], tmp[2], tmp[3]))
                            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=color)
                            self.rel[tmpId] = id_index

                for i in range(1, len(class_name)+1):
                    color = self.relc[i]
                    self.listbox2.insert(END, class_name[i-1])
                    self.listbox2.itemconfig(self.listbox2.size() - 1, fg=color)

        else:
            os.mkdir(self.write_dir)
            # add class_name
            if self.num == 0:
                for i in range(len(class_name)):
                    self.addObj()

    def saveImage(self):
        shutil.rmtree(self.write_dir)
        os.mkdir(self.write_dir)
        for bbox, idx in zip(self.bboxList, self.bboxIdList):
            id_index = self.rel[idx]
            with open(os.path.join(self.write_dir, str(id_index) + '.txt'), 'a') as f:
                f.write(','.join(map(str, bbox)) + '\n')
        with open(os.path.join(self.outDir, '.col.txt'), 'w') as f:
            for k, v in self.relc.items():
                f.write('%d,%s\n' % (k, v))
        with open(os.path.join(self.outDir, '.num.txt'), 'w') as f:
            f.write(str(self.num))
        print('Image No. %d saved' % self.cur)

    def mouseClick(self, event):
        sel = self.listbox2.curselection()
        if len(sel) != 1:
            tkMessageBox.showerror("Error!", message="The specified bbox must be linked to an obj index!")
            self.mainPanel.delete(self.bboxId)
            self.STATE['click'] = 0
            return
        for index, e in enumerate(class_name):
            if e == self.listbox2.get(sel[0]):
                self.selected_obj = index + 1
        #self.selected_obj = int(self.listbox2.get(sel[0]))

        #for v in self.rel.values():
        #    if v == self.selected_obj:
        #        tkMessageBox.showerror("Error!", message="A obj index only links to one bbox!")
        #        self.mainPanel.delete(self.bboxId)
        #        self.STATE['click'] = 0
        #        return

        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)

            self.listbox.insert(END, '(%d, %d, %d, %d)' % (x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=self.relc[self.selected_obj])
            self.rel[self.bboxId] = self.selected_obj
            self.listbox2.selection_clear(0, self.listbox2.size())
            self.bboxId = None
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'],
                                                            event.x, event.y, width=2,
                                                            outline=self.relc[self.selected_obj])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        tmpId = self.bboxIdList[idx]
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)
        self.rel.pop(tmpId)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
        self.rel.clear()

    def addObj(self):
        self.num += 1
        id_index = self.num
        color = COLORS[id_index % len(COLORS)]
        self.relc[id_index] = color
        self.listbox2.insert(END, class_name[id_index-1])
        self.listbox2.itemconfig(self.listbox2.size() - 1, fg=color)

    def delObj(self):
        sel = self.listbox2.curselection()
        if len(sel) != 1:
            return
        idx = sel[0]
        id_index = int(self.listbox2.get(idx))
        is_linked = False
        for i in self.rel.values():
            if i == id_index:
                is_linked = True
        if is_linked:
            tkMessageBox.showerror("Error!", message="There is a bbox linked to this obj, delete the bbox first!")
            return
        self.listbox2.delete(idx)

    def clearObj(self):
        self.listbox2.delete(0, self.listbox2.size())
        for k in self.rel.keys():
            self.rel[k] = None

    def prevImage(self, event = None):
        self.listbox2.selection_clear(0, self.listbox2.size())
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.listbox2.selection_clear(0, self.listbox2.size())
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        self.listbox2.selection_clear(0, self.listbox2.size())
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()
