#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import os

def find(args):
    annodir = os.path.join(args.voc_root, 'Annotations')
    imgdir = os.path.join(args.voc_root, 'JPEGImages')
    annoIDs = [x[:-4] for x in os.listdir(annodir) if x.endswith('.xml')]
    jpgIDs = [x[:-4] for x in os.listdir(imgdir) if x.endswith('.jpg')]

    unique_img = []
    unique_anno = []

    for jpgID in jpgIDs:
        if jpgID not in annoIDs:
            unique_img.append(jpgID)

    for annoID in annoIDs:
        if annoID not in jpgIDs:
            unique_anno.append(annoID)

    if len(unique_img) > 0:
        print('More image:')
        for imgID in sorted(unique_img):
            print(imgID)

    if len(unique_anno) > 0:
        print('More anno:')
        for annoID in sorted(unique_anno):
            print(annoID)

def main(args):
    find(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find unique filename in Annotations and JPEGImages')
    # addarg here
    parser.add_argument('--voc_root', default='', type=str, help='input voc_like dataset root')
    args = parser.parse_args()
    main(args)
