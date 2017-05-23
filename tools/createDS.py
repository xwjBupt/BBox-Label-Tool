#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, six
import codecs
import string
import datetime
import commands

CONF = {
    'basedir': os.curdir,
    'dataset_name': 'default',
    'year': 'default',
    'image_path': '/home/xxoo/Pictures',
    'dataset_save_path': '/home/xxoo/data/',
    'classes_name':'none',
    'if_single':False
}

_DEFAULT_PATH = os.curdir 
_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "templates")
if six.PY3:
    str_compat = str
else:
    str_compat = unicode

def _input_compat(prompt): 
    if six.PY3:
        r = input(prompt)
    else:
        r = raw_input(prompt)
    return r

def ask(question, answer=str_compat, default=None, l=None):
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
            'Argument `answer` must be str_compat, bool, or integer')

def checkDir(imgDir, dstDir):
    exts = ['.jpg', '.JPG'] 
    files = os.listdir(imgDir)
    flag = False
    for ext in exts:
        for f in files:
            if f.endswith(ext):
                flag = True
    if flag == False:
        raise ValueError, "No found image in image directory: {}".format(imgDir)

    if not os.path.exists(dstDir):
        os.makedirs(dstDir)

def createJPEGImages():
    ds_path = os.path.join(CONF['dataset_save_path'], CONF['dataset_name']+CONF['year'], 'JPEGImages')
    if os.path.exists(ds_path):
        print "{} exists".format(ds_path)
        return

    os.makedirs(ds_path)
    ext = os.listdir(CONF['image_path'])[0][-4:]
    imgfiles = [os.path.join(CONF['image_path'], x) for x in os.listdir(CONF['image_path']) if x.endswith(ext)] 
    print "Create {}...".format(ds_path)
    for enum, src in enumerate(imgfiles):
        dst = os.path.join(ds_path, '{:0>6}.jpg'.format(enum+1))
        cmd = 'ln -s {} {}'.format(src, dst)
        (status, output) = commands.getstatusoutput(cmd)

def main():

    print '''Welcome to createDS.py.

This script will help you create a VOC-like dataset.

Please answer the following questions. 
    ''' 
    
    cfg_file = os.path.join(os.environ['HOME'], '.bbox_label.txt')
    if os.path.exists(cfg_file):
        with open(cfg_file, 'r') as fid:
            lines = [x.split('\n')[0] for x in fid.readlines()]
            for l in lines:
                key, value = l.split(':')
                CONF[key] = value

    CONF['dataset_name'] = ask("What is dataset name?", str_compat, CONF['dataset_name']) 
    CONF['dataset_name'] = CONF['dataset_name'].upper()
    CONF['year'] = str(datetime.date.today())[:4]
    CONF['image_path'] = ask("Where is the image directory?", str_compat, CONF['image_path']) 
    CONF['dataset_save_path'] = ask("Where do you want to save the dataset?", str_compat, CONF['dataset_save_path']) 
    CONF['classes_name'] = ask("What are classes name(split by comma, eg:apple,banana,orange)?", str_compat, CONF['classes_name']) 
    CONF['if_single'] = ask("If there is only one object(only for one class)?", bool, CONF['if_single']) 

    checkDir(CONF['image_path'], CONF['dataset_save_path'])

    cfg_file = os.path.join(os.environ['HOME'], '.bbox_label.txt')
    with open(cfg_file, 'w') as fid:
        fid.write('dataset_name:{}\n'.format(CONF['dataset_name']))
        fid.write('year:{}\n'.format(CONF['year']))
        fid.write('image_path:{}\n'.format(CONF['image_path']))
        fid.write('dataset_save_path:{}\n'.format(CONF['dataset_save_path']))
        fid.write('classes_name:{}\n'.format(CONF['classes_name']))
        fid.write('if_single:{}\n'.format(CONF['if_single']))
        fid.write('current_index:{}\n'.format(0))

    createJPEGImages()

    print "Run python main_voc.py to start labelling images\n\n"

if __name__ == "__main__":
    main()

