import tensorflow as tf
import numpy as np
import pickle
import matplotlib.pyplot as plt

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, concatenate, Conv2D, MaxPooling2D, Conv2DTranspose, Reshape
from tensorflow.keras.layers import Conv3D, Conv3DTranspose, MaxPooling3D, BatchNormalization, Activation
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras import backend as K

Version='v5-1'
XDim=864
YDim=512
ZDim=4
WDim=15

XStokes=875
YStokes=512
ZStokes=4
WStokes=15

XMagfld=875
YMagfld=512
ZMagfld=3

sizeBatch=2
nEpochs=10
nExamples=4200
nValid=1200

pathTrain = '/data/hinode/tfr/train.tfr'  # The TFRecord file containing the training set
pathValid = '/data/hinode/tfr/val.tfr'    # The TFRecord file containing the validation set
pathTest = '/data/hinode/tfr/test.tfr'    # The TFRecord file containing the test set
pathWeight = './data/%s.h5'%(Version)  # The HDF5 weight file generated for the trained model
pathModel = './data/%s.nn'%(Version)  # The model saved as a JSON file
pathLog = '../logs/%s'%(Version)  # The training log

def UNet():
  inputs = Input((WStokes, YDim, XDim, ZStokes))
  #conv1 = Conv3D(64, (WDim, 1, 1), use_bias=False, padding='same')(inputs)
  #conv1 = BatchNormalization()(conv1)
  #conv1 = Activation("relu")(conv1)
  #conv1 = Conv3D(64, (WDim, 1, 1), use_bias=False, padding='same')(conv1)
  #conv1 = BatchNormalization()(conv1)
  #conv1 = Activation("relu")(conv1)
  #conv1 = Conv3D(32, (WDim, 1, 1), activation='relu', padding='same')(inputs)
  conv1 = Conv3D(16, (WDim, 3, 3), activation='relu', padding='same')(inputs)
  conv1 = Conv3D(16, (WDim, 3, 3), activation='relu', padding='same')(conv1)
  pool1 = MaxPooling3D(pool_size=(1, 2, 2))(conv1)
  #conv1 = Conv3D(16, (WDim, 3, 3), activation='relu', padding='same')(conv1)
  #conv1 = MaxPooling3D(pool_size=(WDim, 1, 1))(conv1)
  #conv1 = Reshape((YDim, XDim, 32))(conv1)
  #conv1 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv1)
  #conv1 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv1)
  #pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

  conv2 = Conv3D(32, (WDim, 3, 3), activation='relu', padding='same')(pool1)
  conv2 = Conv3D(32, (WDim, 3, 3), activation='relu', padding='same')(conv2)
  pool2 = MaxPooling3D(pool_size=(1, 2, 2))(conv2)
  #conv2 = Conv2D(32, (3, 3), activation='relu', padding='same')(pool1)
  #conv2 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv2)
  #pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

  conv3 = Conv3D(64, (WDim, 3, 3), activation='relu', padding='same')(pool2)
  conv3 = Conv3D(64, (WDim, 3, 3), activation='relu', padding='same')(conv3)
  pool3 = MaxPooling3D(pool_size=(1, 2, 2))(conv3)
  #conv3 = Conv2D(64, (3, 3), activation='relu', padding='same')(pool2)
  #conv3 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv3)
  #pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

  #conv4 = Conv2D(64, (3, 3), activation='relu', padding='same')(pool3)
  #conv4 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv4)
  #pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

  #conv5 = Conv2D(64, (3, 3), activation='relu', padding='same')(pool4)
  #conv5 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv5)
  #pool5 = MaxPooling2D(pool_size=(2, 2))(conv5)

  #conv6 = Conv2D(128, (3, 3), activation='relu', padding='same')(pool5)
  #conv6 = Conv2D(128, (3, 3), activation='relu', padding='same')(conv6)
  conv4 = Conv3D(128, (1, 3, 3), activation='relu', padding='same')(pool3)
  conv4 = Conv3D(128, (1, 3, 3), activation='relu', padding='same')(conv4)

  up5 = concatenate([Conv3DTranspose(128, (1, 2, 2), strides=(1, 2, 2), padding='same')(conv4), conv3], axis=4)
  conv5 = Conv3D(128, (1, 3, 3), activation='relu', padding='same')(up5)
  conv5 = Conv3D(128, (1, 3, 3), activation='relu', padding='same')(conv5)
  #up7 = concatenate([Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(conv6), conv5], axis=3)
  #conv7 = Conv2D(128, (3, 3), activation='relu', padding='same')(up7)
  #conv7 = Conv2D(128, (3, 3), activation='relu', padding='same')(conv7)

  #up8 = concatenate([Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(conv7), conv4], axis=3)
  #conv8 = Conv2D(64, (3, 3), activation='relu', padding='same')(up8)
  #conv8 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv8)

  #up9 = concatenate([Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(conv8), conv3], axis=3)
  #conv9 = Conv2D(64, (3, 3), activation='relu', padding='same')(up9)
  #conv9 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv9)

  #up10 = concatenate([Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(conv9), conv2], axis=3)
  #conv10 = Conv2D(64, (3, 3), activation='relu', padding='same')(up10)
  #conv10 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv10)
  up6 = concatenate([Conv3DTranspose(64, (1, 2, 2), strides=(1, 2, 2), padding='same')(conv5), conv2], axis=4)
  conv6 = Conv3D(64, (1, 3, 3), activation='relu', padding='same')(up6)
  conv6 = Conv3D(64, (1, 3, 3), activation='relu', padding='same')(conv6)

  #up11 = concatenate([Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(conv10), conv1], axis=3)
  #conv11 = Conv2D(32, (3, 3), activation='relu', padding='same')(up11)
  #conv11 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv11)
  up7 = concatenate([Conv3DTranspose(32, (1, 2, 2), strides=(1, 2, 2), padding='same')(conv6), conv1], axis=4)
  conv7 = Conv3D(32, (1, 3, 3), activation='relu', padding='same')(up7)
  conv7 = Conv3D(32, (1, 3, 3), activation='relu', padding='same')(conv7)

  #conv12 = Conv2D(ZMagfld, (1, 1), activation='linear')(conv11)
  conv8 = Conv3D(ZMagfld, (1, 1, 1), activation='linear')(conv7)
  conv8 = MaxPooling3D(pool_size=(WDim, 1, 1))(conv8)
  conv8 = Reshape((YDim, XDim, ZMagfld))(conv8)

  model = Model(inputs=[inputs], outputs=[conv8])

  model.compile(optimizer=Adam(lr=1e-5), loss='mse', metrics=['mse'])

  print(model.summary())

  return model


def train():
  K.set_image_data_format('channels_last')  # TF dimension ordering in this code
  featdef = {
    #'magfld': tf.FixedLenSequenceFeature(shape=[YMagfld*XMagfld*ZMagfld], dtype=tf.string, allow_missing=True),
    #'stokes': tf.FixedLenSequenceFeature(shape=[YStokes*XStokes*ZStokes], dtype=tf.string, allow_missing=True)
    'magfld': tf.FixedLenSequenceFeature(shape=[], dtype=tf.float32, allow_missing=True),
    'stokes': tf.FixedLenSequenceFeature(shape=[], dtype=tf.float32, allow_missing=True),
#    'name':   tf.FixedLenFeature(shape=[], dtype=tf.string)
    }
        
  def _parse_record(example_proto, clip=False):
    """Parse a single record into x and y images"""
    example = tf.parse_single_example(example_proto, featdef)
    #x = tf.decode_raw(example['stokes'], tf.float32)
    x = example['stokes']
    x = tf.reshape(x, (WStokes, YStokes, XStokes, ZStokes))
    x = tf.slice(x, (0, 0, 0, 0), (WStokes, YDim, XDim, ZStokes))
    
    #y = tf.decode_raw(example['magfld'], tf.float32)
    y = example['magfld']
    y = tf.reshape(y, (YMagfld, XMagfld, ZMagfld))
    y = tf.slice(y, (0, 0, 0), (YDim, XDim, ZMagfld))

#    name = example['name']

#    return x, y, name
    return x, y

  #construct a TFRecordDataset
  dsTrain = tf.data.TFRecordDataset(pathTrain).map(_parse_record)
  dsTrain = dsTrain.prefetch(sizeBatch)
  dsTrain = dsTrain.shuffle(4*sizeBatch)
  #dsTrain = dsTrain.map(map_func=_parse_record)
  dsTrain = dsTrain.repeat()
  dsTrain = dsTrain.batch(sizeBatch)

  dsValid = tf.data.TFRecordDataset(pathValid).map(_parse_record)
  #dsValid = dsValid.shuffle()
  dsValid = dsValid.prefetch(sizeBatch)
  #dsValid = dsValid.map(map_func=_parse_record)
  dsValid = dsValid.repeat()
  dsValid = dsValid.batch(sizeBatch)

  #dsTest = tf.data.TFRecordDataset(pathTest).map(_parse_record)
  #dsTest = dsValid.repeat(30)
  #dsTest = dsValid.shuffle(10).batch(sizeBatch)

  print('-'*30)
  print('Creating and compiling model...')
  print('-'*30)
  model = UNet()
  callbacks = [
      tf.keras.callbacks.ModelCheckpoint(pathWeight, verbose=1, monitor='val_loss', save_best_only=True),
      tf.keras.callbacks.TensorBoard(log_dir=pathLog)
  ]

  print('-'*30)
  print('Fitting model...')
  print('-'*30)

  #print(dsTrain)
  history = model.fit(dsTrain, validation_data=dsValid, validation_steps=int(np.ceil(nValid/sizeBatch)), steps_per_epoch=int(np.ceil(nExamples/sizeBatch)), epochs=nEpochs, verbose=1, callbacks=callbacks)
  #history = model.fit(dsTrain, validation_data=dsValid, epochs=nEpochs, verbose=1, callbacks=callbacks)

  # serialize model to JSON
  model_serial = model.to_json()
  with open(pathModel, "w") as yaml_file:
    yaml_file.write(model_serial)

  #Y = model.predict(dsTest, steps=1)
  #image = Y[0,:,:,0]
  
  #fig = plt.figure(num='Level 2 - Predicted')

  #plt.gray()
  #plt.imshow(image)
  #plt.show()
  #plt.close(fig)

print(tf.__version__)
train()
