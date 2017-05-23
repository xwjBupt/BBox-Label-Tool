#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
python createSplit.py
'''
import os, sys
import xml.etree.ElementTree as ET

CFG_FILE = '.bbox_label.txt'

def createSplit():
    cfg_file = os.path.join(os.environ['HOME'], CFG_FILE)
    if not os.path.exists(cfg_file):
        print "Please create dataset using tools/createDS.py first."
        return
    cfg = {}
    with open(cfg_file, 'r') as fid:
        for line in [x.split('\n')[0] for x in fid.readlines()]:
            key, value = line.split(':')
            cfg[key] = value

    root = os.path.join(cfg['dataset_save_path'], cfg['dataset_name']+cfg['year'])
    imgPath = os.path.join(root, 'JPEGImages')
    if not os.path.exists(imgPath):
        print "Please create JPEGImages."
        return
    annoPath = os.path.join(root, 'Annotations')
    if not os.path.exists(annoPath):
        print "Please create Annotations."
        return
    if len(os.listdir(imgPath)) != len(os.listdir(annoPath)):
        print "[Warning]"
        print "Incomplete annotations, split dataset may be incomplete."
        print "You'd better finish label task and then create split dataset\n"

    splitPath = os.path.join(root, 'ImageSets/Main')
    if not os.path.exists(splitPath):
        os.makedirs(splitPath)

    def get_filenames(classname):
        filenames = []
        files = sorted([x for x in os.listdir(annoPath) if not x.startswith('.')])
        for f in files:
            tree = ET.parse(os.path.join(annoPath, f))
            objs = tree.findall('object')
            if classname in [x.find('name').text.lower().strip() for x in objs]:
                filenames.append(f[:-4])
        return filenames

    def createImageSet(filenames, classname):
        # shuffle filenames
        amount = len(filenames)
        trainval = int(amount*0.8)
        train = int(amount*0.8*0.8)

        def write2file(filetype, classname, left, right=-1):
            with open('{}/{}_{}.txt'.format(splitPath, classname, filetype), 'w') as fid:
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

    def converge():
        for t in ['trainval', 'train', 'val', 'test']:
            files = [x for x in os.listdir(splitPath) if x.endswith('_{}.txt'.format(t))]
            lines = []
            for f in files:
                with open(os.path.join(splitPath, f), 'r') as fid:
                    lines += [x[:7]+'\n' for x in fid.readlines()]
            with open(os.path.join(splitPath, '{}.txt'.format(t)), 'w') as fid:
                for line in lines:
                    fid.write(line)

    class_names = [x for x in cfg['classes_name'].split(',')]  #['insulator', 'hammer', 'tower', 'nest', 'text']
    for name in class_names:
        print 'create {} dataset'.format(name)
        filenames = get_filenames(name)  # find image_ind that contains current class
        createImageSet(filenames, name)
    converge()

    print 'Done!'

def main():
    createSplit()

if __name__ == "__main__":
    main()
