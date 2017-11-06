#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import os, sys
import xml.etree.ElementTree as ET
import random
import shutil
import tqdm

CFG_FILE = os.path.join(os.environ['HOME'], '.bbox_label.txt')

def createSplit(args):
    cfg_file = args.cfg_file 
    if not os.path.exists(cfg_file):
        print("Please create dataset using tools/createDS.py first.")
        return
    cfg = {}
    with open(cfg_file, 'r') as fid:
        for line in [x.split('\n')[0] for x in fid.readlines()]:
            key, value = line.split(':')
            cfg[key] = value

    root = os.path.join(cfg['dataset_save_path'], cfg['dataset_name']+cfg['year'])
    imgPath = os.path.join(root, 'JPEGImages')

    if not os.path.exists(imgPath):
        print("Please create JPEGImages.")
        return

    annoPath = os.path.join(root, 'Annotations')
    if not os.path.exists(annoPath):
        print("Please create Annotations.")
        return

    imgfiles = sorted([os.path.join(imgPath, x) for x in sorted(os.listdir(imgPath)) if x.endswith('.jpg')])
    annofiles = sorted([os.path.join(annoPath, x) for x in sorted(os.listdir(annoPath)) if x.endswith('.xml')])
    if len(imgfiles) != len(annofiles):
        print("[Warning]")
        print("Incomplete annotations, split dataset may be incomplete.")
        print("You'd better finish label task and then create split dataset\n")

    splitPath = os.path.join(root, 'ImageSets/Main')
    if os.path.exists(splitPath):
        shutil.rmtree(splitPath)
    os.makedirs(splitPath)

    def get_filenames(classname):
        filenames = []
        files = sorted([x for x in os.listdir(annoPath) if not x.startswith('.')])
        t = tqdm.tqdm()
        t.total = len(files)
        for f in files:
            t.update()
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
            write_list = []
            if right == -1:
                for name in filenames[left : ]:
                    write_list.append(name)
            else:
                for name in filenames[left : right]:
                    write_list.append(name)
            with open('{}/{}_{}.txt'.format(splitPath, classname, filetype), 'w') as fid:
                for name in sorted(write_list):
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
                    for line in fid.readlines():
                        if line[:7] not in lines:
                            lines += line[:7] 
            with open(os.path.join(splitPath, '{}.txt'.format(t)), 'w') as fid:
                for line in lines:
                    fid.write(line+'\n')

    class_names = [x for x in cfg['classes_name'].split(',')] 
    for name in class_names:
        print('Creating {} dataset...'.format(name))
        print('Fetching filenames of {}...'.format(name))
        filenames = get_filenames(name)  # find image_ind that contains current class
        if args.shuffle:
            random.shuffle(filenames)
        print('Writing to files...')
        createImageSet(filenames, name)
    print('Converging...')
    converge()
    print('Done!')

def main(args):
    createSplit(args)

def str2bool(s):
    return s in ['True', '1', 't', 'T', 'y', 'Y']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split voc-like dataset into train/val/test.')
    parser.add_argument('--cfg_file', default=CFG_FILE, type=str, help='BBox-Label-Tool config file')
    parser.add_argument('--shuffle', default=True, type=str2bool, help='if using shuffle')
    args = parser.parse_args()
    main(args)
