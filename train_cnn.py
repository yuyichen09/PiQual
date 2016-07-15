from scipy import ndimage, misc
import numpy as np
import os
import cPickle as pickle
import pandas as pd

from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.layers.core import Flatten, Dense, Dropout
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD

ava_table = pd.read_pickle('filtered_ava.p')
X = pickle.load( open("images_224.p", "rb"))

num_training = 9000
num_test = 1000
X_train = np.hstack(X).reshape(10000,224,224,3)
Y_train = ava_table.ix[:, "good":].as_matrix()

mask = range(num_training, num_training + num_test)
X_test = X_train[mask].transpose(1,2,3,0)
Y_test = Y_train[mask]

mask = range(num_training)
X_train = X_train[mask].transpose(1,2,3,0)
Y_train = Y_train[mask]

weights_path = os.path.join(os.getcwd(), "vgg16_weights.h5")

model = Sequential()
model.add(ZeroPadding2D((1,1),input_shape=(3,224,224)))
model.add(Convolution2D(64, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(64, 3, 3, activation='relu', trainable=False))
model.add(MaxPooling2D((2,2), strides=(2,2)))

model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(128, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(128, 3, 3, activation='relu', trainable=False))
model.add(MaxPooling2D((2,2), strides=(2,2)))

model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(256, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(256, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(256, 3, 3, activation='relu', trainable=False))
model.add(MaxPooling2D((2,2), strides=(2,2)))

model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(512, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(512, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(512, 3, 3, activation='relu', trainable=False))
model.add(MaxPooling2D((2,2), strides=(2,2)))

model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(512, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(512, 3, 3, activation='relu', trainable=False))
model.add(ZeroPadding2D((1,1)))
model.add(Convolution2D(512, 3, 3, activation='relu', trainable=False))
model.add(MaxPooling2D((2,2), strides=(2,2)))

model.add(Flatten())
model.add(Dense(4096, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(4096, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(1000, activation='softmax'))

model.load_weights(weights_path)

model.layers.pop()
model.add(Dense(2, activation='softmax'))

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train.T, Y_train,validation_split=0.1)
score = model.evaluate(X_test.T, Y_test)

model.save_weights('ava_vgg.h5')
print 
print score
print
print "Predictions"
print model.predict(X[0].reshape(1,3,224,224))
print model.predict(X[1].reshape(1,3,224,224))
print model.predict(X[2].reshape(1,3,224,224))
print model.predict(X[3].reshape(1,3,224,224))

filepath = os.path.join(os.getcwd(), "forest.jpg")
image = ndimage.imread(filepath, mode="RGB")
image_resized = misc.imresize(image, (224, 224))
print model.predict(image_resized.reshape(1,3,224,224))

filepath = os.path.join(os.getcwd(), "test.jpg")
image = ndimage.imread(filepath, mode="RGB")
image_resized = misc.imresize(image, (224, 224))
print model.predict(image_resized.reshape(1,3,224,224))



def image_to_pickle():
  ava_path = "dataset/AVA/data/"
  ava_data_path = os.path.join(os.getcwd(), ava_path)
  count = 10000#len(os.listdir(ava_data_path))
  filtered_ava = pd.read_pickle('filtered_ava.p')

  images = np.empty(count, dtype=object)
  print "Loading Images..."
  i=0
  count=10000
  invalid_indices = []
  for index, row in filtered_ava.iterrows():
    if i >= count:
      break
    if (i % 1000) == 0:
      print "Now processing " + str(i) + "/" + str(count)
    filename = str(index) + ".jpg"
    filepath = os.path.join(ava_data_path, filename)
    try:
      image = ndimage.imread(filepath, mode="RGB")
      image_resized = misc.imresize(image, (224, 224))
      images[i] = image_resized
      i=i+1
    except IOError:
      invalid_indices.append(index)
      print filename + " at position " + str(i) + "is missing or invalid."

  filtered_ava.drop(invalid_indices)
  # filtered_ava.save_pickle('filtered_ava.p')
  pickle.dump(images, open("images_224.p", "wb"))
