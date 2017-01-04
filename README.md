BBox-Label-Tool modify by sequence labeling
===============

A simple tool for labeling object bounding boxes in images, implemented with Python Tkinter.

Data Organization
-----------------
LabelTool  
|  
|--main.py   *# source code for the tool*  
|  
|--Images/   *# direcotry containing the images to be labeled*  
|  
|--Labels/   *# direcotry for the labeling results*    

Dependency
----------
python 2.7 win 32bit
PIL-1.1.7.win32-py2.7

Startup
-------
$ python main.py

Usage
-----
1. Input the image dictory address(only for .jpg, but you can change it in code), and click 'Load'. The images along with first read will be loaded.
2. To create a seq. object, select the obj. and to draw a new bounding box as the original tool. Note that every bounding box should link to an object, every object links to one bounding box at most.
  - To cancel the bounding box while drawing, just press <Esc>.
  - To delete a existing bounding box, select it from the listbox, and click 'Delete' at the bottom of bounding box listbox.
  - To delete a existing obejct, simply click 'Delete' at the bottom of obj index listbox. Only unlinked object can be delete.
3. After finishing one image, click 'Next' to advance. Likewise, click 'Prev' to reverse. Or, input the index and click 'Go' to navigate to an arbitrary image.
  - The labeling result will be saved if and only if the 'Next' button is clicked.
