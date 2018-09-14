
from __future__ import print_function
import argparse
import os, sys
import xml.etree.ElementTree as ET
import random
import shutil
import tqdm

import xml.dom.minidom

root = '/media/xwj/Data/DataSet/minishipVOC/SHIPFAST2018/Annotations'
annofiles = sorted([os.path.join(root, x) for x in sorted(os.listdir(root)) if x.endswith('.xml')])

for ann in annofiles:

        # TODO
        # xml文件读取操作

        # 将获取的xml文件名送入到dom解析
        dom = xml.dom.minidom.parse(ann)
        root = dom.documentElement
        # 获取标签对name/pose之间的值
        name = root.getElementsByTagName('filename')

        # 重命名class name
        for i in range(len(name)):
            print (name[i].firstChild.data)
            name[i].firstChild.data = '00001.jpg'
            print (name[i].firstChild.data)
        # 保存修改到xml文件中
        with open(ann, 'w') as fh:
            dom.writexml(fh)
            print('写入name/pose OK!')

