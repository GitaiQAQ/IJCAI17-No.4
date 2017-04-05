# -*- coding: utf-8 -*-
"""
Created on Tue Apr 04 16:04:28 2017

@author: aa
"""

import numpy as np
import cv2
from matplotlib import pyplot as plt
img = cv2.imread('tt.png')
gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
corners = cv2.goodFeaturesToTrack(gray,25,0.01,10)
corners = np.int0(corners)
for i in corners:
    x,y = i.ravel()
    cv2.circle(img,(x,y),3,255,-1)
plt.imshow(img),plt.show()