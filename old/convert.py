#!/usr/bin/env python

# -*- coding: utf-8 -*-

'''
Convert BBox-Label to VOC2007 format
Usage: python convert.py [annotation_path] [image_path]
'''
import sys, os
import copy
import Image
import commands
import xml.etree.ElementTree as ET

#names = ['insulator', 'hammer', 'tower', 'nest', 'text']
names = ['cervical']

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

def getImageSize(imgPath, fileNum):
    filename = os.path.join(imgPath, "{}.jpg".format(fileNum))
    return Image.open(filename).size

def createAnnotation(filepath, imgPath):
    if not os.path.exists('Annotations'):
        os.makedirs('Annotations')
    else:
        return

    global Annnotation
    global Object
    files = sorted([x for x in os.listdir(filepath) if not x.startswith('.')])
    i = 0
    for filename in files: # annotation/[000000 000001 000002 ...] 
        width, height = getImageSize(imgPath, filename)
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
                    
                    xmin = min(x1, x2)
                    xmax = max(x1, x2)
                    ymin = min(y1, y2)
                    ymax = max(y1, y2)

                    xmin = max(0, xmin) + 1
                    xmax = min(width, xmax)
                    ymin = max(0, ymin) + 1 
                    ymax = min(height, ymax)

                    newObj = copy.deepcopy(Object).format(name, xmin, ymin, xmax, ymax)

                    objs += newObj
        newAnno = copy.deepcopy(Annnotation).format(filename, width, height, objs)

        with open('Annotations/{}.xml'.format(filename), 'w') as fid:
            fid.write(newAnno)

        sys.stdout.flush()
        sys.stdout.write('writing {}/{}\r'.format(i, len(files)))
        i += 1
    print '\nFinish!'

def createJPEGImages(filepath, imgPath):
    files = sorted([x for x in os.listdir(filepath) if not x.startswith('.')])

    if not imgPath.endswith('/'):
        imgPath += '/'
    if not os.path.exists('JPEGImages'):
        os.makedirs('JPEGImages')
    else:
        return
    os.chdir('JPEGImages')

    i = 1
    for filename in files: 
        cmd = 'ln -s {}{:0>6}.jpg {:0>6}.jpg'.format(imgPath, filename, filename)
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            print "Error when run \"ln\""
            return

        sys.stdout.flush()
        sys.stdout.write('create link {}/{}\r'.format(i, len(files)))
        i += 1 # set i = 0 before looping
    print '\nFinish!' 
    os.chdir('../')

def createImageSets():
    if not os.path.exists('JPEGImages'):
        print "Please create JPEGImages."
        return
    if not os.path.exists('Annotations'):
        print "Please create Annotations."
        return
    if not os.path.exists('ImageSets/Main'):
        os.makedirs('ImageSets/Main')

    #filenames = sorted([x[:-4] for x in os.listdir('JPEGImages') if not x.startswith('.') and x.endswith('.jpg')])

    def createImageSet(filenames, classname): 
        amount = len(filenames)
        trainval = int(amount*0.8)
        train = int(amount*0.8*0.8)

        def write2file(filetype, classname, left, right=-1):
            with open('ImageSets/Main/{}_{}.txt'.format(classname, filetype), 'w') as fid:
                if right == -1:
                    for name in filenames[left : ]:
                        fid.write('{} 1\n'.format(name))
                else:
                    for name in filenames[left : right]:
                        fid.write('{} 1\n'.format(name))

        write2file('trainval', classname, 0, trainval)
        write2file('train', classname, 0, train)
        write2file('val', classname, train, trainval)
        write2file('test', classname, trainval)

    def get_filenames(classname):
        filenames = []
        files = sorted([x for x in os.listdir('Annotations') if not x.startswith('.')])
        for f in files:
            tree = ET.parse('Annotations/{}'.format(f))
            objs = tree.findall('object')
            if classname in [x.find('name').text.lower().strip() for x in objs]:
                filenames.append(f[:-4])
        return filenames

    class_names = ['insulator', 'hammer', 'tower', 'nest', 'text']
    for name in class_names:
        print 'create {} dataset'.format(name)
        filenames = get_filenames(name)
        createImageSet(filenames, name)
    print 'Done!'

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return
    createAnnotation(sys.argv[1], sys.argv[2])
    createJPEGImages(sys.argv[1], sys.argv[2])
    createImageSets()

if __name__ == "__main__":
    main()
