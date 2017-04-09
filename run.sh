#!/usr/bin/env bash

LABEL_PATH=Labels/imageset2_1200
IMAGE_PATH=~/data/dianwang/imageset2_1200 

./convert.py $LABEL_PATH $IMAGE_PATH

VOC_PATH=~/data/VOCdevkit
if [ -d $VOC_PATH/DIAN2007 ];then
    rm $VOC_PATH/DIAN2007 -r
fi
mkdir $VOC_PATH/DIAN2007

if [ -d Annotations ] && [ -d ImageSets ] && [ -d JPEGImages ];then
    mv Annotations $VOC_PATH/DIAN2007/
    mv ImageSets $VOC_PATH/DIAN2007/
    mv JPEGImages $VOC_PATH/DIAN2007/
fi
