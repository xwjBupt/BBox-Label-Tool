#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
python describeDataset.py [imdb name]
eg: voc_2007_trainval, dian_2016_trainval, nest_2017_trainval
'''

import sys, os
this_dir = os.path.join(os.getcwd(), os.path.dirname(__file__))
root = os.path.join(this_dir, '../')
sys.path.insert(0, root)

from objdect.dataset import datasets
from objdect.train.prepare_roidb import get_training_roidb
import numpy as np
import matplotlib.pyplot as plt

def _convert2classes_roidb(roidb, imdb):
    results = {}
    for (name, each_class_ind) in imdb._class_to_ind.items(): 
        if each_class_ind == 0:
            continue
        bboxes = []
        for roi in roidb:
            for ind, label in enumerate(roi['gt_classes']):
                if label== each_class_ind:
                    bboxes.append(roi['boxes'][ind])
        results[name] = np.array(bboxes)
        print(name, results[name].shape)
    return results


def getColor(values, color):
    if color == 'r':
        return [ plt.cm.Reds(x) for x in values]

    elif color == 'g':
        return [ plt.cm.Greens(x) for x in values]

    elif color == 'b':
        return [ plt.cm.Blues(x) for x in values]

    else:
        print("Unknown color: {}".format(color))
        return None


def drawBar(data, imdb_name):
    assert len(data) > 0
    fig, ax = plt.subplots()
    n_groups = len(list(data[0].keys()))
    index = list(range(n_groups))
    bar_width = 0.22

    opacity = 0.4

    names=['num', 'scale', 'ratio']
    color=['r', 'b', 'g']
    for ind, each in enumerate(data):
        if ind == 0:
            norm_values = [x*1./max(each.values()) for x in list(each.values())]
            rect = plt.bar([x for x in index], norm_values, bar_width, alpha=opacity, \
                    color=color[ind] , label=names[ind])
            for i in index:
                plt.text( i-bar_width/2, norm_values[i], '{}'.format(list(each.values())[i]))

        else:
            twoValues = np.array(list(each.values())).astype(np.float)
            assert twoValues.shape[1] == 2

            norm_values = twoValues[:,0] * 1. / np.max(twoValues[:,0]) # mean 
            norm_values_std = twoValues[:,1] * 1. / np.max(twoValues[:,1]) \
                    if np.max(twoValues[:,1]) != 0 \
                    else np.ones((twoValues.shape[0])) # std 

            rect = plt.bar([x + ind*(bar_width) for x in index], norm_values, bar_width, alpha=opacity, \
                    color=getColor(norm_values_std, color[ind]), label=names[ind])

            for i in index:
                plt.text( i+ind*bar_width-bar_width/2, norm_values[i], '%.1f'%(list(each.values())[i][0]))
                plt.text( i+ind*bar_width-bar_width/2, norm_values_std[i]/2, '%.1f'%(list(each.values())[i][1]))
    
            
    plt.title(imdb_name)
    plt.xticks(index, list(data[0].keys()))
    plt.grid(axis='y')
    plt.legend()

    plt.show()


def describeDataset(argv):
    imdb_name = argv[1]
    dataset_path = os.path.join(os.environ['HOME'], 'data/VOCdevkit')
    imdb = datasets.get_imdb_common(imdb_name, dataset_path)

    n_classes = imdb.num_classes
    roidb = get_training_roidb(imdb, False)
    class_bboxes = _convert2classes_roidb(roidb, imdb)

    

    num_boxes = {}
    size_boxes = {}
    ratio_boxes = {}
    for (k, v) in list(class_bboxes.items()):
        # num
        num_boxes[k] =  v.shape[0]
        # size
        size = np.sqrt( (v[:,2] - v[:,0]) * (v[:,3] - v[:,1]) )
        size_boxes[k] = [np.mean(size), np.std(size)]
        # ratio
        ratio = (v[:,2] - v[:,0]) * 1.0 / (v[:,3] - v[:,1]) 
        ratio_boxes[k] = [np.mean(ratio), np.std(ratio)]

    #print sorted(num_boxes.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    drawBar([num_boxes, size_boxes, ratio_boxes], imdb_name)


def main():
    import sys
    if len(sys.argv) != 2:
        print(__doc__)
        return
    describeDataset(sys.argv)

if __name__ == "__main__":
    raise NotImplementedError
    main()
