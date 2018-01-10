#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import os, sys
import numpy as np
import xml.etree.ElementTree as ET
import cv2
import tqdm
import six

if six.PY3:
    str_compat = str
else:
    str_compat = unicode


def ask(question, answer=str_compat, default=None, l=None):
    def _input_compat(prompt):
        if six.PY3:
            return input(prompt) 
        else:
            return raw_input(prompt)

    if answer == str_compat:
        r = ''
        while True:
            if default:
                r = _input_compat('> {0} [{1}] '.format(question, default))
            else:
                r = _input_compat('> {0} '.format(question, default))

            r = r.strip()

            if len(r) <= 0:
                if default:
                    r = default
                    break
                else:
                    print('You must enter something')
            else:
                if l and len(r) != l:
                    print('You must enter a {0} letters long string'.format(l))
                else:
                    break
        return r
    elif answer == bool:
        r = None
        while True:
            if default is True:
                r = _input_compat('> {0} (Y/n) '.format(question))
            elif default is False:
                r = _input_compat('> {0} (y/N) '.format(question))
            else:
                r = _input_compat('> {0} (y/n) '.format(question))

            r = r.strip().lower()

            if r in ('y', 'yes'):
                r = True
                break
            elif r in ('n', 'no'):
                r = False
                break
            elif not r:
                r = default
                break
            else:
                print("You must answer 'yes' or 'no'")
        return r
    elif answer == int:
        r = None
        while True:
            if default:
                r = _input_compat('> {0} [{1}] '.format(question, default))
            else:
                r = _input_compat('> {0} '.format(question))

            r = r.strip()

            if not r:
                r = default
                break

            try:
                r = int(r)
                break
            except:
                print('You must enter an integer')
        return r
    else:
        raise NotImplemented(
            'Argument  must be str_compat, bool, or integer')


def delete_file(xmlfiles, root):
    imgfile = os.path.join(os.path.dirname(root), 'JPEGImages', '{}.jpg')
    for xmlfile in xmlfiles:
        filename = os.path.split(xmlfile)[-1][:-4]
        img = cv2.imread(imgfile.format(filename))
        cv2.imshow('img', img)

        ch = cv2.waitKey(0) & 0xff
        if ch == ord('d'):
            #os.remove(xmlfile)
            #os.remove(imgfile.format(filename))
            print('delete xml and jpg of {}'.format(filename))
        if ch == 27: #ord('q')
            break


def checkAnnotations(args):
    root = os.path.abspath(args.anno_dir)
    xmls = sorted([os.path.join(root, x) for x in os.listdir(root) if x.endswith('.xml')])

    t = tqdm.tqdm()
    t.total = len(xmls)

    bad_list = []
    empty_xmls = []

    for xmlfile in xmls:
        t.update()
        tree = ET.parse(xmlfile)    
        width = int(tree.find('size').find('width').text)
        height = int(tree.find('size').find('height').text)
    
        boxes = []
        objs = tree.findall('object')
        for index, obj in enumerate(objs):
            name = obj.find('name').text.lower()
            bbox = obj.find('bndbox')
            x1 = int(bbox.find('xmin').text) - 1
            y1 = int(bbox.find('ymin').text) - 1
            x2 = int(bbox.find('xmax').text) - 1
            y2 = int(bbox.find('ymax').text) - 1
            box = [x1, y1, x2, y2]
            boxes.append(box)
        if len(boxes) == 0:
            empty_xmls.append(xmlfile)
            continue

        boxes = np.array(boxes)

        try:
            # check xmax > xmin, ymax > ymin
            assert (boxes[:,2] > boxes[:,0]).all(), "xmax <= xmin in {}".format(xmlfile)
            assert (boxes[:,3] > boxes[:,1]).all(), "ymax <= ymin in {}".format(xmlfile)
        except Exception as e:
            bad_list.append(xmlfile)

        try:
            # check xmin >= 0, xmax < width, ymin >= 0, ymax < heigth
            assert (boxes[:,0] >= 0).all() and (boxes[:,2] < width).all(), "xmin >=0 and xmax < width in {}".format(xmlfile)
            assert (boxes[:,1] >= 0).all() and (boxes[:,3] < height).all(), "ymin >=0 and ymax < height in {}".format(xmlfile)
        except Exception as e:
            bad_list.append(xmlfile)

        # check when flipping roi
        boxes2 = boxes.copy()
        boxes2[:,0] = width - boxes[:, 2] - 1
        boxes2[:,2] = width - boxes[:, 0] - 1
        try:
            assert (boxes2[:,2] >= boxes2[:,0]).all(), "error when flipping {}".format(xmlfile)
        except Exception as e:
            bad_list.append(xmlfile)
    
    if len(bad_list) == 0:
        print("no bad xml")
    else:
        print("bad xml:")
        for f in bad_list:
            print(f)

    if len(empty_xmls) == 0:
        print("no empty xml")
    else:
        print("empty xml:")
        for f in empty_xmls:
            print(f)

    print('empty xml sum:', len(empty_xmls))
    if len(empty_xmls) > 0:
        delete = ask("if delete empty xmls and its images?", bool, False)
        if delete:
            print('Press <keyboard-d> to delete current jpg and xml')
            delete_file(empty_xmls, root)


def main(args):
    checkAnnotations(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check annotations in voc-like dataset.')
    parser.add_argument('--anno_dir', required=True, type=str, help='annotation xml file directory.')
    args = parser.parse_args()
    main(args)
