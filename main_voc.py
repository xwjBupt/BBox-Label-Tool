#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014
# Revised:     Duino
#-------------------------------------------------------------------------------

from __future__ import division
from __future__ import print_function
try:
    # for Python2
    from Tkinter import *   ## notice capitalized T in Tkinter 
except ImportError:
    # for Python3
    from tkinter import *   ## notice lowercase 't' in tkinter here
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import glob
import shutil
import xml.etree.ElementTree as ET
import copy
import argparse

CFG_FILE = os.path.join(os.environ['HOME'], '.bbox_label.txt')

# xml template
Annnotation = """<annotation>
	<folder>BBoxLabel</folder>
	<filename>{}</filename>
	<source>
		<database>The VOC2007 Database</database>
		<annotation>PASCAL VOC2007</annotation>
		<image>flickr</image>
		<flickrid>341012865</flickrid>
	</source>
	<size>
		<width>{}</width>
		<height>{}</height>
		<depth>3</depth>
	</size>
	<segmented>0</segmented>
        {}
</annotation>
"""
Object = """
	<object>
		<name>{}</name>
		<pose>Left</pose>
		<truncated>0</truncated>
		<difficult>0</difficult>
		<bndbox>
			<xmin>{}</xmin>
			<ymin>{}</ymin>
			<xmax>{}</xmax>
			<ymax>{}</ymax>
		</bndbox>
	</object>
"""

# colors for the bboxes
COLORS = ['#90EE90', '#B22222', '#DDA0DD', '#00FF00', '#008000', '#D2691E', '#DC143C',
          '#C0C0C0', '#FFE4C4', '#32CD32', '#8B008B', '#6495ED', '#8A2BE2', '#EE82EE',
          '#FF00FF', '#006400', '#7FFF00', '#FF00FF', '#0000CD', '#FF8C00', '#FFEFD5',
          '#C71585', '#7CFC00', '#9370DB', '#6A5ACD', '#B0C4DE', '#4169E1', '#ADFF2F',
          '#FF1493', '#DB7093', '#BA55D3', '#C71585', '#9400D3', '#FF6347', '#90EE90',
          '#FFFF00', '#E6E6FA', '#0000FF', '#808000', '#BDB76B', '#FFFFE0', '#808080',
          '#696969', '#40E0D0', '#CD853F', '#008080', '#48D1CC', '#8B4513', '#FFF5EE',
          '#FAF0E6', '#98FB98', '#00FFFF', '#87CEEB', '#00BFFF', '#B0E0E6', '#00FA9A',
          '#F5FFFA', '#F0E68C', '#F5DEB3', '#008B8B', '#8FBC8F', '#FF0000', '#F08080',
          '#66CDAA', '#3CB371', '#2E8B57', '#A52A2A', '#B22222', '#AFEEEE', '#FFF8DC',
          '#DAA520', '#FFFAF0', '#FDF5E6', '#F4A460', '#D2691E']
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master, args):
        self.args = args

        # load cfg_file
        self.cfg = {}
        self.read_cfg()
        print("cfg:")
        print(self.cfg)

        # read imglist if necessary
        self.imglist = []
        if args.imglist != '':
            self.imglist = [int(x.strip().split(' ')[0]) for x in open(args.imglist, 'r').readlines()][::-1]
            

        # set up the main frame
        self.parent = master
        self.parent.title("Lable tool for {}".format(self.cfg['dataset_name']))
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.imageDir = os.path.join(self.cfg['dataset_save_path'], self.cfg['dataset_name']+self.cfg['year'], 'JPEGImages')
        self.annoDir = os.path.join(self.cfg['dataset_save_path'], self.cfg['dataset_name']+self.cfg['year'], 'Annotations')
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 1
        self.total = 0
        self.category = 0
        self.tkimg = None
        self.imageDstHeight = 600
        self.imageScale = None
        self.imageOriginHeight = 0
        self.imageOriginWidth = 0
        self.btn_bg = PhotoImage(file=os.path.join(os.path.dirname(__file__), 'btn_bg.png'))

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxBtnIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.rel = dict()  # key: window_id, value: label id(1,2,3,4,5...)
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

        ## set default entry
        #import sys
        #if len(sys.argv) == 2:
        #    self.entry.insert(0, sys.argv[1])
        self.entry.insert(0, self.cfg['image_path'])

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
        self.btnDe2 = Button(self.frame, text='Add')
        self.btnDe2.grid(row=3, column=2, sticky=W + E + N)
        self.btnDe3 = Button(self.frame, text='Delete')
        self.btnDe3.grid(row=4, column=2, sticky=W+E+N)
        self.btnDe2.pack_forget() # hide Add button
        self.btnDe3.pack_forget() # hide Add button

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

    def read_cfg(self):
        cfg_file = self.args.cfg
        if not os.path.exists(cfg_file):
            raise IOError("No found config file {}, run tool/createDS.py first.\n Or you can set config file in \"main_voc.py [cfg_path]\"".format(cfg_file))

        with open(cfg_file, 'r') as fid:
            for line in [x.split('\n')[0] for x in fid.readlines()]:
                name, value = line.split(':')
                self.cfg[name] = value

    def write_cfg(self):
        cfg_file = self.args.cfg
        if not os.path.exists(cfg_file):
            raise IOError("No found config file {}, run tool/createDS.py first.\n Or you can set config file in \"main_voc.py [cfg_path]\"".format(cfg_file))

        with open(cfg_file, 'w') as fid:
            for (name, value) in self.cfg.items():
                fid.write(name)
                fid.write(':')
                fid.write(value)
                fid.write('\n')

    def loadDir(self, dbg=False):
        if not dbg:
            if not os.path.exists(self.annoDir):
                os.makedirs(self.annoDir)
        else:
            self.imageDir = ''
        if not os.path.isdir(self.imageDir):
            messagebox.showerror("Error!", message="The specified dir doesn't exist!")
            return
        # get image list
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPG'))
        if len(self.imageList) == 0:
            self.imageList = glob.glob(os.path.join(self.imageDir, '*.png'))
        if len(self.imageList) == 0:
            self.imageList = glob.glob(os.path.join(self.imageDir, '*.PNG'))

        self.imageList.sort()
        if len(self.imageList) == 0:
            print('No .JPG(jpg png PNG) images found in the specified dir')
            return

        # default to the 1st image in the collection
        self.cur = int(self.cfg['current_index'])
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = self.annoDir 
        if not os.path.exists(self.outDir):
            os.makedirs(self.outDir)

        self.class_name = []
        self.num = 0
        self.addObjs()

        for i in range(1, len(self.class_name)+1):
            color = self.relc[i]
            #self.listbox2.insert(END, self.class_name[i-1]) # if add, there will be double class name in the list box
            self.listbox2.itemconfig(self.listbox2.size() - 1, fg=color)

        self.loadImage()
        print('%d images loaded from %s' % (self.total, self.imageDir))

    def loadImage(self):
        # load image
        if self.cur > len(self.imageList):
            print("Finish")
            return
        
        if self.imglist != '':
            imagepath = self.imageDir + "/{:0>6}.jpg".format(self.cur)
        else:
            imagepath = self.imageList[self.cur-1] # self.cur is 1-based

        img = Image.open(imagepath)
        self.imageOriginWidth = img.size[0]
        self.imageOriginHeight = img.size[1]
        self.imageScale = self.imageDstHeight * 1.0  / img.size[1]
        img = img.resize((int(img.size[0] * self.imageScale), int(img.size[1] * self.imageScale)), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text="%06d/%06d" % (self.cur, self.total))

        #self.write_dir = os.path.join(self.outDir, os.path.split(imagepath)[-1].split('.')[0])
   
        # load labels
        self.clearBBox()
        filename = os.path.join(self.annoDir, '{:0>6}.xml'.format(self.cur))
        if not os.path.exists(filename):
            return

        bboxes, labels = self.readXML(filename)

        for box, label in zip(bboxes, labels):
            id_index = -1 # start from 1
            for index, name in enumerate(self.class_name):
                if name == label:
                    id_index = index + 1
            assert (id_index > 0), "Unknown label name in Annotations/{}.xml".format(self.imageList[self.cur])
            color = self.relc[id_index]

            tmpId = self.mainPanel.create_rectangle(int(self.imageScale * box[0]), 
                                                    int(self.imageScale * box[1]),
                                                    int(self.imageScale * box[2]), 
                                                    int(self.imageScale * box[3]),
                                                    width=2,
                                                    outline=color)
            #tmp_btnId = self.createButton(self.mainPanel, (int(self.imageScale * box[0]), int(self.imageScale * box[1])))
            self.bboxList.append(tuple(box))
            self.bboxIdList.append(tmpId)
            #self.bboxBtnIdList.append(tmp_btnId)
            self.listbox.insert(END, '(%d, %d, %d, %d)' % (box[0], box[1], box[2], box[3]))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=color)
            self.rel[tmpId] = id_index


            ## add class_name
            #if self.num == 0:
            #    for i in range(len(class_name)):
            #        self.addObj()
            #    if not os.path.exists(os.path.join(self.outDir, '.col.txt')):
            #        with open(os.path.join(self.outDir, '.col.txt'), 'w') as f:
            #            for k, v in self.relc.items():
            #                f.write('%d,%s\n' % (k, v))
            #        with open(os.path.join(self.outDir, '.num.txt'), 'w') as f:
            #            f.write(str(self.num))

    def saveImage(self):
        """
        self.bboxList -> ***.xml
        """
        if args.imglist != '':
            filename = "{:0>6}".format(self.cur)
        else:
            imagepath = self.imageList[self.cur-1]
            filename = os.path.split(imagepath)[1][:-4]

        width, height = self.imageOriginWidth, self.imageOriginHeight
        objs = ""
        print(self.bboxList)
        for bbox, idx in zip(self.bboxList, self.bboxIdList):
            id_index = self.rel[idx]
            name = self.class_name[id_index - 1]
            assert(len(bbox) == 4)
            x1 = bbox[0]
            y1 = bbox[1]
            x2 = bbox[2]
            y2 = bbox[3]
            xmin = min(x1, x2)
            xmax = max(x1, x2)
            ymin = min(y1, y2)
            ymax = max(y1, y2)

            xmin = max(1, xmin+1)
            xmax = min(width, xmax+1)
            ymin = max(1, ymin+1) 
            ymax = min(height, ymax+1)
            newObj = copy.deepcopy(Object).format(name, xmin, ymin, xmax, ymax)
            objs += newObj
        newAnno = copy.deepcopy(Annnotation).format(filename, width, height, objs)
        xmlfile = self.annoDir + '/{}.xml'.format(filename)

        if os.path.exists(xmlfile):
            os.remove(xmlfile)
        with open(xmlfile, 'w') as fid:
            fid.write(newAnno)
        print('Image No. %d saved to %s' % (self.cur, xmlfile))

        #if not os.path.exists(os.path.join(self.outDir, '.col.txt')):
        #    with open(os.path.join(self.outDir, '.col.txt'), 'w') as f:
        #        for k, v in self.relc.items():
        #            f.write('%d,%s\n' % (k, v))
        #    with open(os.path.join(self.outDir, '.num.txt'), 'w') as f:
        #        f.write(str(self.num))

        self.cfg['current_index'] = str(self.cur)
        self.write_cfg()

    def mouseClick(self, event):
        sel = self.listbox2.curselection()
        if len(sel) != 1 and len(self.class_name) > 1:
            messagebox.showerror("Error!", message="The specified bbox must be linked to an obj index!")
            self.mainPanel.delete(self.bboxId)
            self.STATE['click'] = 0
            return
        elif len(self.class_name) == 1:
            sel = [self.listbox2.index(0)]

        for index, e in enumerate(self.class_name):
            if e == self.listbox2.get(sel[0]):
                self.selected_obj = index + 1

        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)

            x1 = int( x1 / self.imageScale )
            y1 = int( y1 / self.imageScale )
            x2 = int( x2 / self.imageScale )
            y2 = int( y2 / self.imageScale )

            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)

            self.listbox.insert(END, '(%d, %d, %d, %d)' % (x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=self.relc[self.selected_obj])
            self.rel[self.bboxId] = self.selected_obj
            #self.listbox2.selection_clear(0, self.listbox2.size())
            self.bboxId = None
            if self.SINGLE:
                self.nextImage()
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

    def delBBox(self, idx=None):
        sel = self.listbox.curselection()
        if len(sel) != 1 and idx == None:
            return
        if idx == None:
            idx = int(sel[0])
        if idx == -1:
            return
        tmpId = self.bboxIdList[idx]
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxList.pop(idx)
        self.bboxIdList.pop(idx)
        #self.mainPanel.delete(self.bboxBtnIdList[idx])
        #self.bboxBtnIdList.pop(idx)
        self.listbox.delete(idx)
        self.rel.pop(tmpId)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
        self.rel.clear()

    def addObjs(self):
        self.class_name = self.cfg['classes_name'].split(',')
        self.num = len(self.class_name)
        for id_index in range(1, self.num+1):
            color = COLORS[id_index % len(COLORS)]
            self.relc[id_index] = color
            self.listbox2.insert(END, self.class_name[id_index-1])
            self.listbox2.itemconfig(self.listbox2.size() - 1, fg=color)
        if self.num == 1 and self.cfg['if_single'] == 'True':
                self.SINGLE = True
        else:
            self.SINGLE = False

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
            messagebox.showerror("Error!", message="There is a bbox linked to this obj, delete the bbox first!")
            return
        self.listbox2.delete(idx)

    def clearObj(self):
        self.listbox2.delete(0, self.listbox2.size())
        for k in self.rel.keys():
            self.rel[k] = None

    def prevImage(self, event = None):
        self.clearBBoxButtons()
        self.listbox2.selection_clear(0, self.listbox2.size())
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.clearBBoxButtons()
        self.listbox2.selection_clear(0, self.listbox2.size())
        self.saveImage()

        if self.args.imglist != '':
            if len(self.imglist) == 0:
                print('Finish')
            else:
                self.cur = self.imglist.pop()
                self.loadImage()
        else:
            if self.cur < self.total:
                self.cur += 1
                self.loadImage()
            else:
                print("Finish")

    def gotoImage(self):
        self.listbox2.selection_clear(0, self.listbox2.size())
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()
    
    def createButton(self, canvas, pos, _text="Del"):
        button = Button(self.frame, text=_text, anchor=W, command=lambda: self.delBBoxByBtn(pos))
        button.configure(width=10, activebackground="#33B5E5", relief=FLAT)
        return canvas.create_window(pos[0], pos[1], anchor=NW, window=button, height=30, width=50)

    def clearBBoxButtons(self):
        for i in self.bboxBtnIdList:
            self.mainPanel.delete(i)

    def delBBoxByBtn(self, pos):
        eps = 8
        idx = -1
        for i in range(0, len(self.bboxList)):
            if abs(self.bboxList[i][0] - pos[0]*1.0 / self.imageScale) < eps and abs(self.bboxList[i][1] - pos[1]*1.0 / self.imageScale) < eps:
                idx = i
                break
        print("delete: ", idx, pos)
        self.delBBox(idx)

    def readXML(self, filename):
        """
        return bboxes, labels
        """
        assert os.path.exists(filename)

        tree = ET.parse(filename)
        objs = tree.findall('object')
        num_objs = len(objs)
        boxes = [] 
        labels = []

        # Load object bounding boxes into a data frame.
        for ix, obj in enumerate(objs):
            bbox = obj.find('bndbox')
            # Make pixel indexes 0-based
            x1 = int(bbox.find('xmin').text) - 1
            y1 = int(bbox.find('ymin').text) - 1
            x2 = int(bbox.find('xmax').text) - 1
            y2 = int(bbox.find('ymax').text) - 1

            x1 = min(x1, x2)
            y1 = min(y1, y2)
            x2 = max(x1, x2)
            y2 = max(y1, y2)

            boxes.append([x1, y1, x2, y2])
            labels.append(obj.find('name').text.lower())

        return boxes, labels

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Label tool')
    parser.add_argument('--cfg', default=CFG_FILE, type=str, help='bbox config file')
    parser.add_argument('--imglist', default='', type=str, help='set image list, only load image from the list')
    args = parser.parse_args()

    root = Tk()
    tool = LabelTool(root, args)
    root.mainloop()

