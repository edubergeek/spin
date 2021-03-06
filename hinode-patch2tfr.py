from random import shuffle
import glob
import os
import sys
import numpy as np
import fs
from fs import open_fs
import tensorflow as tf
import matplotlib.pyplot as plt

dirsep = '/'
csvdelim = ','
#basePath='/d/hinode/data'
basePath='./data'
#basePath='./data/20140202_041505'
#basePath='./data/20120703_134836'
#basePath='./data/20130114_123005'
imageText = "image"
inputText = "*.fits"
outputText = "out"
trainCSV = "./spin.csv"

printName = False

PXDim=64
PYDim=64
PX=13
PY=8

XDim=875
YDim=512
ZDim=4
YZDim=3

WDim=112
WStart=0
WStep=1

pTest = 0.1
pVal = 0.1
nCopies=1

train_filename = './tfr/trn-patch.tfr'  # the TFRecord file containing the training set
val_filename = './tfr/val-patch.tfr'      # the TFRecord file containing the validation set
test_filename = './tfr/tst-patch.tfr'    # the TFRecord file containing the test set

def chunkstring(string, length):
  return (string[0+i:length+i] for i in range(0, len(string), length))

# filter images on mean level 1 intensity pixel value and position on sun
# True means don't use the image and False means OK to use the image
def isFiltered(img, meta):
  #if np.std(img) >= 1e-4:
  #if np.std(img) < 1e-4:
  yc = float(meta['YCEN'])
  if yc >= -600.0 and yc <= 600.0:
    xc = float(meta['XCEN'])
    if xc >= -600.0 and xc <= 600.0:
      for r in range(0, PYDim):
        if np.min(img[r,:]) == np.max(img[r,:]):
          return True
      for c in range(0, PXDim):
        if np.min(img[:,c]) == np.max(img[:,c]):
          return True
      return False

  return True

# filter images on mean level 1 intensity pixel value
def Classification(img, meta):
  if np.std(img) >= 1e-4:
    return 1
  if np.std(img) < 5e-5:
    return 0
  return -1

normMean = [12317.92913, 0.332441335, -0.297060628, -0.451666942]
normStdev = [1397.468631, 65.06104869, 65.06167056, 179.3232721]
def normalize(img, idx):
  img = img / normMean[idx]
  img /= normStdev[idx]
  return img

def load_fits(filnam):
  from astropy.io import fits

  hdulist = fits.open(filnam)
  meta = {}
  #gen = chunkstring(hdulist[0].header, 80)
  #for keyval in gen:
  #  for x in keyval.astype('U').split('\n'):
  #    meta = x
  #    print(meta)
  #  #meta.update( dict(x.split('=') for x in np.array_str(keyval, 80).split('\n')) )
  h = list(chunkstring(hdulist[0].header, 80))
  for index, item in enumerate(h):
    m = str(item)
    mh = list(chunkstring(m, 80))
    #print(mh)
    for ix, im in enumerate(mh):
      #print(index, ix, im)
      mm = im.split('/')[0].split('=')
      if len(mm) == 2:
        #print(index, ix, mm[0], mm[1])
        meta[mm[0].strip()] = mm[1].strip()
  nAxes = int(meta['NAXIS'])
  if nAxes == 0:
    # should be checking metadata to verify this is a level2 image
    nAxes = 3
    if len(hdulist[1].data.shape) < 2:
      data = np.empty((1, 1, 3))
    else:
      maxy, maxx = hdulist[1].data.shape
      data = np.empty((maxy, maxx, 3))
      data[:,:,0] = hdulist[1].data
      data[:,:,1] = hdulist[2].data
      data[:,:,2] = hdulist[3].data
  else:
    data = hdulist[0].data
  data = np.nan_to_num(data)
  #img = data.reshape((maxy, maxx, maxz))
  #img = np.rollaxis(data, 1)
  img = data
  if nAxes == 3:
    maxy, maxx, maxz = data.shape
  else:
    maxy, maxx = data.shape
    maxz = 0
  hdulist.close
  return maxy, maxx, maxz, meta, img

# Generator function to walk path and generate 1 SP3D image set at a time
def process_sp3d(basePath):
  prevImageName=''
  level = 0
  skipping = False
  fsDetection = open_fs(basePath)
  img=np.empty((WDim,YDim,XDim,ZDim))
  WInd = list(range(WStart,WStart+WDim*WStep,WStep))
  for path in fsDetection.walk.files(search='breadth', filter=[inputText]):
    # process each "in" file of detections
    inName=basePath+path
    #print('Inspecting %s'%(inName))
    #open the warp warp diff image using "image" file
    sub=inName.split(dirsep)
    obsName=sub[-3]
    imageName=sub[-2]
    if imageName != prevImageName:
      if prevImageName != '':
        # New image so wrap up the current image
        # if not skipping it's ok to release the prior images for further processing
        if not skipping:
          # Flip image Y axis
          #img = np.flip(img, axis=1)
          yield img, fitsName, level, wl, meta, obsName
        skipping = False
      # Initialize for a new image
      #print('Parsing %s - %s'%(imageName, path))
      prevImageName = imageName
      fitsName=sub[-1]
      # reset image to zeros
      img[:,:,:,:]=0
    #else:
    #  print('Appending %s to %s'%(path, imageName))
    #imgName=basePath+dirsep+pointing+dirsep+imageText
    #imgName=inName
    #byteArray=bytearray(np.genfromtxt(imgName, 'S'))
    #imageFile=byteArray.decode()
    imageFile=inName
    # if level2 was skipped then skip level1 as well
    if skipping:
      #print('Skipping %s'%(imageName))
      continue
    if printName:
      print("Opening image file %s"%(imageFile))
    height, width, depth, imageMeta, imageData = load_fits(imageFile)
    if height == 1 and width == 1:
      #print('Skipping %s'%(imageName))
      skipping = True
      continue
    # now the pixels are in the array imageData shape height X width X 1
    # read the truth table from the "out" file
    #for k, v in imageMeta.items():
    #  print(k,v)
    if 'INVCODE' in imageMeta:
      # level 2 FITS file
      level = 2
      dimY, dimX, dimZ = imageData.shape
      # crop to maximum height
      dimY = min(dimY, YDim)
      # crop to maximum width
      dimX = min(dimX, XDim)
      dimW = 0
      #dimZ = 0
      # we should have 3 dimensions, the azimuth, altitude and intensity
      wl = (float(imageMeta['LMIN2']) + float(imageMeta['LMAX2'])) / 2.0
      img[0,0:dimY,0:dimX,0:dimZ] = imageData[0:dimY,0:dimX,0:dimZ]
      meta = imageMeta
    else:
      # level 1 FITS file
      level = 1
      x = int(imageMeta['SLITINDX'])
      if x < XDim:
        wl = float(imageMeta['CRVAL1']) + (WStart*float(imageMeta['CDELT1']))
        dimZ, dimY, dimX = imageData.shape
        # crop to maximum height
        dimY = min(dimY, YDim)
        # crop to maximum width
        dimX = min(dimX, XDim)
        dimW = WDim
        # concatenate the next column of data
        # 4, 512, 112
        # 1, 512, 9
        a=np.reshape(imageData[0,:dimY,:],(dimY, dimX))
        a = a[:,WInd]
        img[0:dimW,0:dimY,x,0] = np.transpose(a)
        a=np.reshape(imageData[1,:dimY,:],(dimY, dimX))
        a = a[:,WInd]
        img[0:dimW,0:dimY,x,1] = np.transpose(a)
        a=np.reshape(imageData[2,:dimY,:],(dimY, dimX))
        a = a[:,WInd]
        img[0:dimW,0:dimY,x,2] = np.transpose(a)
        a=np.reshape(imageData[3,:dimY,:],(dimY, dimX))
        a = a[:,WInd]
        img[0:dimW,0:dimY,x,3] = np.transpose(a)
        meta = imageMeta

  if prevImageName != '':
    # New image so wrap up the current image
    # Flip image Y axis
    if not skipping:
      #img = np.flip(img, axis=1)
      yield img, fitsName, level, wl, meta, obsName
    fsDetection.close()
  
def _floatvector_feature(value):
  return tf.train.Feature(float_list=tf.train.FloatList(value=value))

def _float_feature(value):
  return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))

def _int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def _bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

np.random.seed()

# open the TFRecords file
train_writer = tf.python_io.TFRecordWriter(train_filename)

# open the TFRecords file
val_writer = tf.python_io.TFRecordWriter(val_filename)

# open the TFRecords file
test_writer = tf.python_io.TFRecordWriter(test_filename)

# find input files in the target dir "basePath"
# it is critical that pairs are produced reliably first level2 then level1
# for each level2 (Y) file
i = nActive = nQuiet = nExamples = nTrain = nVal = nTest = naTrain = naVal = naTest = nqTrain = nqVal = nqTest = 0

img=np.empty((WDim,YDim,XDim,ZDim))
#nz=np.empty((ZDim))

for image, name, level, line, meta, obsname in process_sp3d(basePath):
  if level == 2:
    # image is the level2 magnetic field prediction per pixel (Y)
    #ya=np.reshape(image[0,0:YDim,0:XDim,0:3],(YDim*XDim*3))
    ya=image[0,0:YDim,0:XDim,0:3].copy()
    nExamples += 1
    #if nExamples > 768:
    #  printName = True
    #print(nExamples, name, level, line)
  else:
    # image is the level1 Stokes params for several WLs of the line of interest (X)
    # filter image using first wavelength (axis 0) and SP=I (axis 3)

    #print(name, level, line)
    xa=image.copy()
    #xa=np.reshape(img,(WDim*YDim*XDim*ZDim))
    #yp = np.empty((PYDim, PXDim, YZDim))
    #xp = np.empty((ZDim, PYDim, PXDim, WDim))
    #print(ya.shape)
    #print(xa.shape)
    for yi in range(0, PY):
      for xi in range(0, PX):
        y = yi * PYDim
        x = xi * PXDim
        #print('y1=%d x1=%d y2=%d x2=%d'%(y,x,y+PYDim,x+PXDim))
        yp=np.reshape(ya[y:y+PYDim,x:x+PXDim,:], (PYDim*PXDim*YZDim))
        xp=np.reshape(xa[:,y:y+PYDim,x:x+PXDim,:], (WDim*PYDim*PXDim*ZDim))
        img_filt = xa[0,y:y+PYDim,x:x+PXDim,0]
        img_filt = normalize(img_filt, 0)
        if isFiltered(img_filt, meta):
          continue
        classification = Classification(img_filt, meta)
        if classification < 0:
          continue
        roll = np.random.random()
        patch=obsname+'(%d,%d)'%(y,x)

        if False:
          imI = xa[56,y:y+PYDim,x:x+PXDim,0]
          plt.gray()
          plt.imshow(imI)
          plt.title(patch)
          plt.show()

          mfI = ya[y:y+PYDim,x:x+PXDim,0]
          plt.gray()
          plt.imshow(mfI)
          plt.title(patch)
          plt.show()

        if classification:
          active = '1'
        else:
          active = '0'
        xcen = float(meta['XCEN'])
        ycen = float(meta['YCEN'])
        xoff = float(xi)
        yoff = float(yi)
        dateobs = meta['DATE_OBS']
        feature = {
          'magfld': _floatvector_feature(yp.tolist()),
          'stokes': _floatvector_feature(xp.tolist()),
          'xcen': _float_feature(xcen),
          'ycen': _float_feature(ycen),
          'xoff': _float_feature(xoff),
          'yoff': _float_feature(yoff),
          'name': _bytes_feature(obsname.encode('utf-8')),
          'dateobs': _bytes_feature(dateobs.encode('utf-8')),
          'active': _bytes_feature(active.encode('utf-8'))
        }
        # Create an example protocol buffer
        example = tf.train.Example(features=tf.train.Features(feature=feature))

        # roll the dice to see if this is a train, val or test example
        # and write it to the appropriate TFRecordWriter
        i += 1

        # Serialize to string and write on the file
        if classification:
          if roll >= (pVal + pTest):
            train_writer.write(example.SerializeToString())
            naTrain += 1
            nTrain += 1
            if not naTrain % 100 and i > 0:
              print('%d ACTIVE: %d train, %d validate, %d test.'%(nExamples, naTrain, naVal, naTest))
              sys.stdout.flush()
          elif roll >= pTest:
            val_writer.write(example.SerializeToString())
            naVal += 1
            nVal += 1
          else:
            test_writer.write(example.SerializeToString())
            naTest += 1
            nTest += 1
          nActive += 1
          print('%d Active: %s %f'%(nActive, patch, np.std(img_filt)), flush=True)
        elif nQuiet < nActive:
          if roll >= (pVal + pTest):
            train_writer.write(example.SerializeToString())
            nqTrain += 1
            nTrain += 1
            if not nqTrain % 100 and i > 0:
              print('%d QUIET: %d train, %d validate, %d test.'%(nExamples, nqTrain, nqVal, nqTest))
              sys.stdout.flush()
          elif roll >= pTest:
            val_writer.write(example.SerializeToString())
            nqVal += 1
            nVal += 1
          else:
            test_writer.write(example.SerializeToString())
            nqTest += 1
            nTest += 1
          nQuiet += 1
          print('%d Quiet: %s %f'%(nQuiet, patch, np.std(img_filt)), flush=True)

#  if nTrain >= 100000:
#    break

train_writer.close()
val_writer.close()
test_writer.close()
if i > 0:
  print('%d examples: %d'%(nExamples))
  print('%d patches: %d train, %d validate, %d test'%(i, nTrain, nVal, nTest))
  print('100% = %03.1f%% train + %03.1f%%validate + %03.1f%%test'%(100.0*nTrain/i, 100.0*nVal/i, 100.0*nTest/i))
sys.stdout.flush()

