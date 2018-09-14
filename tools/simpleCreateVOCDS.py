'''
此文件是此工程的简化版，要求已有对图片进行过标注（图像和标注数量相同）
简易创建一个仿voc格式的数据集




'''

from __future__ import print_function
import argparse
import os, sys
import xml.etree.ElementTree as ET
import random
import shutil
import tqdm




def main():
    root = os.path.join(args.root,'VOCdevkit2007/voc2007')
    splitPath = os.path.join(root, 'ImageSets/Main')
    os.mkdirs(root+'/Annotaions')
    os.mkdirs(root+'/JPEGImages')
    os.makedirs(splitPath)
    imgfiles = sorted([os.path.join(args.imdir, x) for x in sorted(os.listdir(args.imdir)) if x.endswith('.jpg')])
    annofiles = sorted([os.path.join(args.anndir, x) for x in sorted(os.listdir(args.anndir)) if x.endswith('.xml')])




    def createImageSet(filenames, classname,splitPath):
        # shuffle filenames
        amount = len(filenames)
        trainval = int(amount * 0.8)
        train = int(amount * 0.8 * 0.8)

        def write2file(filetype, classname, left, right=-1):
            write_list = []
            if right == -1:
                for name in filenames[left:]:
                    write_list.append(name)
            else:
                for name in filenames[left: right]:
                    write_list.append(name)
            with open('{}/{}_{}.txt'.format(splitPath, classname, filetype), 'w') as fid:
                for name in sorted(write_list):
                    fid.write('{} 1\n'.format(name))

        write2file('trainval', classname, 0, trainval)
        write2file('train', classname, 0, train)
        write2file('val', classname, train, trainval)
        write2file('test', classname, trainval)

    def converge(splitPath):


        for t in ['trainval', 'train', 'val', 'test']:
            files = [x for x in os.listdir(splitPath) if x.endswith('_{}.txt'.format(t))]
            lines = []
            for f in files:
                with open(os.path.join(splitPath, f), 'r') as fid:
                    for line in fid.readlines():
                        if line[:7] not in lines:
                            lines.append(line[:7])
            with open(os.path.join(splitPath, '{}.txt'.format(t)), 'w') as fid:
                for line in lines:
                    fid.write(line + '\n')

    createImageSet(imgfiles, args.classname,splitPath)
    converge(splitPath)


def str2bool(s):
    return s in ['True', '1', 't', 'T', 'y', 'Y']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='simple way to create a voc-like dataset')
    parser.add_argument('--imdir',  type=str, help='images directory')
    parser.add_argument('--anndir',  type=str, help='annotation files')
    parser.add_argument('--shuffle', default=True, type=str2bool, help='if using shuffle')
    parser.add_argument('--root', type=str, help='where to save the dataset')
    parser.add_argument('--classname', type=str, help='classname')
    args = parser.parse_args()
    main(args)