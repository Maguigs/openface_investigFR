#!/usr/bin/env python2
#
####################################
#
# Example to compare images in 2 folders and generate list of matching scores in csv file
# Maelig Jacquet
# 01.06.2020
#
# adapted from https://cmusatyalab.github.io/openface/
#
####################################
#
# Example to compare the faces in two images.
# Brandon Amos
# 2015/09/29
#
# Copyright 2015-2016 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import time

start = time.time()

import argparse
import cv2
import itertools
import os
import shutil

import numpy as np
np.set_printoptions(precision=2)

import openface

from tqdm import tqdm

fileDir = os.path.dirname(os.path.realpath(__file__))
# modelDir = os.path.join(fileDir, '..', 'models')
modelDir = "/root/openface/models"        ### path fixe pour docker sous linux

dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')

parser = argparse.ArgumentParser()

parser.add_argument('imgs', type=str, nargs='+', help="Input images.")
parser.add_argument('--dlibFacePredictor', type=str, help="Path to dlib's face predictor.",
                    default=os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))
parser.add_argument('--networkModel', type=str, help="Path to Torch network model.",
                    default=os.path.join(openfaceModelDir, 'nn4.small2.v1.t7'))
parser.add_argument('--imgDim', type=int,
                    help="Default image dimension.", default=96)
parser.add_argument('--verbose', action='store_true')

args = parser.parse_args()

if args.verbose:
    print("Argument parsing and loading libraries took {} seconds.".format(
        time.time() - start))

start = time.time()
align = openface.AlignDlib(args.dlibFacePredictor)
net = openface.TorchNeuralNet(args.networkModel, args.imgDim)
if args.verbose:
    print("Loading the dlib and OpenFace models took {} seconds.".format(
        time.time() - start))

def checkimg(imgPath, imglist):
    err = 0

    if args.verbose:
        print("Processing {}.".format(imgPath))
    bgrImg = cv2.imread(imgPath)
    if bgrImg is None:
        # print("Unable to load image: {}".format(imgPath))
        err=1
    rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

    if args.verbose:
        print("  + Original size: {}".format(rgbImg.shape))

    start = time.time()
    bb = align.getLargestFaceBoundingBox(rgbImg)
    if bb is None:
        # print("Unable to find a face in: {}".format(imgPath))
        if err == 0:
            err=2

    if args.verbose:
        print("  + Face detection took {} seconds.".format(time.time() - start))

    start = time.time()
    alignedFace = align.align(args.imgDim, rgbImg, bb,
                              landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
    if alignedFace is None:
        # print("Unable to align image: {}".format(imgPath))
        if err == 0:
            err=3

    if args.verbose:
        print("  + Face alignment took {} seconds.".format(time.time() - start))

    start = time.time()

    if err != 0:
        image_error=os.path.basename(imgPath)
        # shutil.move(image_error, "/home/mjacquet/Desktop/")
        imglist.remove(imgPath)

        if not os.path.exists(error_path):
            os.makedirs(error_path)

        error_file = open(error_path + "/errors.txt", "a")

        if err == 1:
            error_file.write("Unable to load image: {}\n".format(imgPath))
            print("Unable to load image: {}".format(image_error))
        elif err == 2:
            error_file.write("Unable to find a face in: {}\n".format(imgPath))
            print("Unable to find a face in: {}".format(image_error))
        elif err == 3:
            error_file.write("Unable to align image: {}\n".format(imgPath))
            print("Unable to align image: {}".format(image_error))



def getRep(imgPath):
    if args.verbose:
        print("Processing {}.".format(imgPath))
    bgrImg = cv2.imread(imgPath)
    if bgrImg is None:
        print("Unable to load image: {}".format(imgPath))
    rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

    if args.verbose:
        print("  + Original size: {}".format(rgbImg.shape))

    start = time.time()
    bb = align.getLargestFaceBoundingBox(rgbImg)
    if bb is None:
        print("Unable to find a face in: {}".format(imgPath))

    if args.verbose:
        print("  + Face detection took {} seconds.".format(time.time() - start))

    start = time.time()
    alignedFace = align.align(args.imgDim, rgbImg, bb,
                              landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
    if alignedFace is None:
        print("Unable to align image: {}".format(imgPath))
    if args.verbose:
        print("  + Face alignment took {} seconds.".format(time.time() - start))

    start = time.time()

    rep = net.forward(alignedFace)
    if args.verbose:
        print("  + OpenFace forward pass took {} seconds.".format(time.time() - start))
        print("Representation:")
        print(rep)
        print("-----\n")
    return rep

# ##### ligne originale : NxN sur toutes les images
# for (img1, img2) in itertools.combinations(args.imgs, 2):               ## extrait 2 images pour faire paire img1 et img2 (args --> parse, voir ligne 53)
#     d = getRep(img1) - getRep(img2)
#     print("Comparing {} with {}.".format(img1, img2))
#     print(
# "  + Squared l2 distance between representations: {:0.3f}".format(np.dot(d, d)))
# #####

## Comparison 1xN with images path 1 versus path 2 + results files .csv

dirimg1 = args.imgs[0]
dirimg2 = args.imgs[1]
results = args.imgs[2]

error_path = os.path.abspath(os.path.join(results, os.pardir)) + "/Errors/"
#print os.path.abspath(os.path.join(results, os.pardir))

fresult = open(results, "w+")
fresult.write("Image 1;Image 2;Score\n")

##### path 1 in terminal
if os.path.isdir(dirimg1):
    listimg1 = []
    listnom1 = []
    for f in os.listdir(dirimg1):
        listimg1.append(dirimg1 + "/" + f )
        listnom1.append(f)
else :
    listimg1=[dirimg1]

#print (os.path.isdir(dirimg2))

## path 2
if os.path.isdir(dirimg2):
    listimg2 = []
    listnom2 = []
    for ff in os.listdir(dirimg2):
        listimg2.append(dirimg2 + "/" + ff )
        listnom2.append(ff)
else :
    listimg2=[dirimg2]

##### process images and adapt list of images to compare by removing error inducing images
with tqdm(total=len(listimg1), desc = 'Checking path1 images') as pbar1:
    for list1 in listimg1:
        checkimg(list1, listimg1)
        pbar1.update(1)

##### remove img in dir 2 if already in dir 1
for element in listnom1:
    if element in listnom2:
        listimg2.remove(dirimg2 + element)
#####

with tqdm(total=len(listimg2), desc = 'Checking path2 images') as pbar2:
    for list2 in listimg2:
        checkimg(list2, listimg2)
    	pbar2.update(1)

#####
tot_comp = len(listimg1) * len(listimg2)
print ("{} comparisons to perform".format(tot_comp))

##### Comparison all images in path 1 versus all in path 2
with tqdm(total=tot_comp, desc = 'Running comparisons') as pbartot:
	for img1 in listimg1 :
	    for img2 in listimg2:
    		nom_img1,_ = os.path.splitext(os.path.basename(img1))               #garder juste le nom ("nom_img1") sans le path ni l'extension (",_")
    		nom_img2,_ = os.path.splitext(os.path.basename(img2))
    		#print (nom_img1 + "      vs      " + nom_img2)

    		d = getRep(img1) - getRep(img2)
    		fresult.write("%s;%s;%.3f\n" % (nom_img1, nom_img2, np.dot(d, d)))

    		pbartot.update(1)
fresult.close()
