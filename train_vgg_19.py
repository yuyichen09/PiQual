from scipy import ndimage, misc
import cv2
import numpy as np
import os
import cPickle as pickle
import pandas as pd
from pandas import HDFStore, DataFrame

import h5py

from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.layers.core import Flatten, Dense, Dropout
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.utils.np_utils import to_categorical
from keras.optimizers import SGD


def VGG_19(weights_path=None,heatmap=False):
    model = Sequential()

    if heatmap:
        model.add(ZeroPadding2D((1,1),input_shape=(3,None,None)))
    else:
        model.add(ZeroPadding2D((1,1),input_shape=(3,224,224)))
    model.add(Convolution2D(64, 3, 3, activation='relu', name='conv1_1'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(64, 3, 3, activation='relu', name='conv1_2'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(128, 3, 3, activation='relu', name='conv2_1'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(128, 3, 3, activation='relu', name='conv2_2'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_1'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_2'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_3'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_4'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_1'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_2'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_3'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_4'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_1'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_2'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_3'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_4'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    if heatmap:
        model.add(Convolution2D(4096,7,7,activation="relu",name="dense_1"))
        model.add(Convolution2D(4096,1,1,activation="relu",name="dense_2"))
        model.add(Convolution2D(1000,1,1,name="dense_3"))
        model.add(Softmax4D(axis=1,name="softmax"))
    else:
        model.add(Flatten())
        model.add(Dense(4096, activation='relu', name='dense_1'))
        model.add(Dropout(0.5))
        model.add(Dense(4096, activation='relu', name='dense_2'))
        model.add(Dropout(0.5))
        model.add(Dense(1000, name='dense_3'))
        model.add(Activation("softmax"))

    if weights_path:
        model.load_weights(weights_path)

    return model

if __name__ == "__main__":

    num_training = 9000
    num_test = 1000
    store = HDFStore('labels.h5')
    # delta = 1
    ava_table = store['labels']
    # X_train = np.hstack(X).reshape(10000,224,224,3)
    # X = pickle.load( open("images_224.p", "rb"))
    h5f = h5py.File('images_224.h5','r')
    X = h5f['images'][:]
    X_train = np.hstack(X).reshape(3,224,224,10000).T

    X_train = X_train.astype('float32')

    Y_train = ava_table.ix[:, "good"].as_matrix()
    Y_train = to_categorical(Y_train, 2)

    mask = range(num_training, num_training + num_test)
    X_test = X_train[mask].transpose(1,2,3,0)
    Y_test = Y_train[mask]

    mask = range(num_training)
    X_train = X_train[mask].transpose(1,2,3,0)
    Y_train = Y_train[mask]

    X_mean = np.mean(X_train)
    X_train -= X_mean
    X_train /= 255

    X_test -= np.mean(X_test)
    X_test /= 255

    weights_path = os.path.join(os.getcwd(), "vgg19_weights.h5")

    model = VGG_19(weights_path)
    model.layers.pop()
    model.layers.pop()
    model.add(Dropout(0.5))
    model.add(Dense(output_dim=2, activation='softmax',name='dense_4'))

    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    model.fit(X_train.T, Y_train,validation_split=0.1, nb_epoch=1)


    model.save_weights('ava_vgg_19.h5')

    score = model.evaluate(X_test.T, Y_test)
    print 
    print('Test score:', score[0])
    print('Test accuracy:', score[1])
    print
    print "Predictions"