#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
import argparse
import os

try:
    import commands
except Exception as e:
    import subprocess as commands
import xml.etree.ElementTree as ET
import tqdm


def resize(args):
    imgfile = os.path.join(args.root, 'JPEGImages/%s.jpg')
    xmlfile = os.path.join(args.root, 'Annotations/%s.xml')
    filenames = [x[:-4] for x in os.listdir(os.path.join(args.root, 'Annotations')) if x.endswith('.xml')]

    imgpath = os.path.join(args.root, 'JPEGImages_{}'.format(args.size))
    xmlpath = os.path.join(args.root, 'Annotations_{}'.format(args.size))
    if not os.path.exists(imgpath):
        os.makedirs(imgpath)
    if not os.path.exists(xmlpath):
        os.makedirs(xmlpath)

    t = tqdm.tqdm()
    t.total = len(filenames)

    for filename in sorted(filenames):
        t.update()
        #cmd = 'convert {} -geometry x{} {}/{}.jpg'.format(imgfile % filename, args.size, imgpath, filename)
        #(status, output) = commands.getstatusoutput(cmd)
        #output = output.split('\n')
        
        tree = ET.parse(xmlfile % filename)
        width = int(tree.find('size').find('width').text)
        height = int(tree.find('size').find('height').text)
        scale = args.size / height

        root = tree.getroot()
        for node in root.iter('height'):
            node.text = str(args.size)
        for name in ['width', 'xmin', 'ymin', 'xmax', 'ymax']:
            for node in root.iter(name):
                new_value = int(int(node.text) * scale)
                node.text = str(new_value)
        tree.write('{}/{}.xml'.format(xmlpath, filename))


def main(args):
    resize(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Resize voc-like image and anno in dataset')
    parser.add_argument('--root', default='', type=str, help='voc-like dataset path')
    parser.add_argument('--size', default=256, type=int, help='dst size in height')
    
    args = parser.parse_args()
    main(args)
