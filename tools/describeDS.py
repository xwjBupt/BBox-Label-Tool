#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import sys, os
import numpy as np
import matplotlib.pyplot as plt
import torch.utils.data as data
import xml.etree.ElementTree as ET


class AnnotationTransform(object):
    """Transforms a VOC annotation into a Tensor of bbox coords and label index
    Initilized with a dictionary lookup of classnames to indexes

    Arguments:
        class_to_ind (dict, optional): dictionary lookup of classnames -> indexes
            (default: alphabetic indexing of VOC's 20 classes)
        keep_difficult (bool, optional): keep difficult instances or not
            (default: False)
        height (int): height
        width (int): width
    """
    def __init__(self, class_to_ind=None, keep_difficult=False):
        self.keep_difficult = keep_difficult

    def __call__(self, target, width, height):
        """
        Arguments:
            target (annotation) : the target annotation to be made usable
                will be an ET.Element
        Returns:
            a list containing lists of bounding boxes  [bbox coords, class name]
        """
        res = []
        for obj in target.iter('object'):
            difficult = int(obj.find('difficult').text) == 1
            if not self.keep_difficult and difficult:
                continue
            name = obj.find('name').text.lower().strip()
            bbox = obj.find('bndbox')

            pts = ['xmin', 'ymin', 'xmax', 'ymax']
            bndbox = []
            for i, pt in enumerate(pts):
                cur_pt = int(bbox.find(pt).text) - 1

                # scale height or width
                #cur_pt = cur_pt / width if i % 2 == 0 else cur_pt / height
                bndbox.append(cur_pt)

            bndbox.append(name)
            res += [bndbox]  # [xmin, ymin, xmax, ymax, name]

            # img_id = target.find('filename').text[:-4]

        return res  # [[xmin, ymin, xmax, ymax, name], ... ]

class VOCDetection(data.Dataset):
    """VOC Detection Dataset Object

    input is image, target is annotation

    Arguments:
        root (string): filepath to VOCdevkit folder.
        image_set (string): imageset to use (eg. 'train', 'val', 'test')
        transform (callable, optional): transformation to perform on the
            input image
        target_transform (callable, optional): transformation to perform on the
            target `annotation`
            (eg: take in caption string, return tensor of word indices)
        dataset_name (string, optional): which dataset to load
            (default: 'VOC2007')
    """

    def __init__(self, root, image_sets, transform=None, target_transform=None,
                 dataset_name='VOC2007'):
        self.rootpath = root
        self.image_sets = image_sets
        self.transform = transform
        self.target_transform = target_transform
        self.name = dataset_name
        self._annopath = os.path.join('%s', 'Annotations', '%s.xml')
        self._imgpath = os.path.join('%s', 'JPEGImages', '%s.jpg')
        self.ids = list()
        for name in self.image_sets:
            for line in open(os.path.join(self.rootpath, 'ImageSets', 'Main', name + '.txt')):
                self.ids.append((self.rootpath, line.strip()))

    def __getitem__(self, index):
        im, gt, h, w = self.pull_item(index)
        return im, gt

    def __len__(self):
        return len(self.ids)

    def pull_item(self, index):
        img_id = self.ids[index]

        target = ET.parse(self._annopath % img_id).getroot()
        img = cv2.imread(self._imgpath % img_id)
        height, width, channels = img.shape
        target = self.target_transform(target, width, height)

        if self.transform is not None:
            target = np.array(target)
            try:
                img, boxes, labels = self.transform(img, target[:, :4], target[:, 4])
            except Exception as e:
                import ipdb
                ipdb.set_trace()
            # to rgb
            img = img[:, :, (2, 1, 0)]
            # img = img.transpose(2, 0, 1)
            target = np.hstack((boxes, np.expand_dims(labels, axis=1)))
        return torch.from_numpy(img).permute(2, 0, 1), target, height, width
        # return torch.from_numpy(img), target, height, width

    def pull_image(self, index):
        '''Returns the original image object at index in PIL form

        Note: not using self.__getitem__(), as any transformations passed in
        could mess up this functionality.

        Argument:
            index (int): index of img to show
        Return:
            PIL img
        '''
        img_id = self.ids[index]
        return cv2.imread(self._imgpath % img_id, cv2.IMREAD_COLOR)

    def pull_anno(self, index):
        '''Returns the original annotation of image at index

        Note: not using self.__getitem__(), as any transformations passed in
        could mess up this functionality.

        Argument:
            index (int): index of img to get annotation of
        Return:
            list:  [img_id, [(label, bbox coords),...]]
                eg: ('001718', [('dog', (96, 13, 438, 332))])
        '''
        img_id = self.ids[index]
        anno = ET.parse(self._annopath % img_id).getroot()
        gt = self.target_transform(anno, 1, 1)
        return img_id[1], gt

    def pull_tensor(self, index):
        '''Returns the original image at an index in tensor form

        Note: not using self.__getitem__(), as any transformations passed in
        could mess up this functionality.

        Argument:
            index (int): index of img to show
        Return:
            tensorized version of img, squeezed
        '''
        return torch.Tensor(self.pull_image(index)).unsqueeze_(0)


def _convert2classes(ds):
    rois_dict = {}
    for i in range(len(ds)):
        _, gt = ds.pull_anno(i)
        for roi in gt:
            if roi[-1] not in rois_dict:
                rois_dict[roi[-1]] = []
            rois_dict[roi[-1]].append(roi[:4])
    results = {}
    for name in rois_dict.keys():
        results[name] = np.array(rois_dict[name])
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


def describeDataset(args):
    ds_name = os.path.basename(args.dataset_path)
    ds = VOCDetection(args.dataset_path, args.split, target_transform=AnnotationTransform())

    print('Reading anno files...')
    class_bboxes = _convert2classes(ds)

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
    drawBar([num_boxes, size_boxes, ratio_boxes], ds_name)


def main(args):
    describeDataset(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Description of voc-like dataset.')
    parser.add_argument('--dataset_path', required=True, type=str, help='dataset directory')
    parser.add_argument('--split', nargs='+', required=True, help='train | trainval | test')
    args = parser.parse_args()
    main(args)
