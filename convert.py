#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Convert BBox-Label to VOC2007 format
Usage: python convert.py [annotation_path]
'''
import sys, os
import copy

Annnotation = """<annotation>
	<folder>DianWang</folder>
	<filename>{}</filename>
	<source>
		<database>The VOC2007 Database</database>
		<annotation>PASCAL VOC2007</annotation>
		<image>flickr</image>
		<flickrid>341012865</flickrid>
	</source>
	<owner>
		<flickrid>Fried Camels</flickrid>
		<name>Jinky the Fruit Bat</name>
	</owner>
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


def convert(filepath):
    if not os.path.exists('Annotations'):
        os.makedirs('Annotations')

    global Annnotation
    global Object
    files = sorted([x for x in os.listdir(filepath) if not x.startswith('.')])
    for filename in files: # annotation/[000000 000001 000002 ...] 
        width = 1000
        height = 1000
        names = ['insulator', 'hammer', 'tower', 'nest', 'text']
        objs = ""
        for obj in sorted(os.listdir( os.path.join(filepath, filename) )): # 000000/[1.txt  2.txt  3.txt  4.txt  5.txt]
            name = names[int(obj[0])-1]
            with open(os.path.join(filepath, filename, obj), 'r') as fid: # open 1.txt
                lines = [x.split('\n')[0] for x in fid.readlines()]
                for box in lines: # multi boxes for one class
                    box = box.split(',')
                    assert(len(box) == 4)
                    x1 = eval(box[0])
                    y1 = eval(box[1])
                    x2 = eval(box[2])
                    y2 = eval(box[3])
                    newObj = copy.deepcopy(Object).format(name, x1, y1, x2, y2)
                    #newObj = Object.format(name, x1, y1, x2, y2)
                    objs += newObj
        newAnno = copy.deepcopy(Annnotation).format(filename, width, height, objs)
        
        with open('Annotations/{}.xml'.format(filename), 'w') as fid:
            fid.write(newAnno)
        print "write to Annotations/{}".format(filename)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return
    convert(sys.argv[1])

if __name__ == "__main__":
    main()
