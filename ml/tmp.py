import pickle
import numpy as np

import pickle
import numpy as np



from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LogisticRegressionCV

from keras.layers import LSTM
from keras.layers import Embedding
from keras.optimizers import RMSprop


from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.utils import np_utils
from keras.engine.topology import Input

from sklearn.metrics import accuracy_score
from keras.layers import Concatenate, Merge

import keras
from keras.utils import to_categorical


model_chords = Sequential()
model_notes = Sequential()

model_chords.add(Embedding(10000, 20, input_length=1, batch_input_shape=(1,1)))
model_notes.add(Embedding(128, 20, input_length=1, batch_input_shape=(1,1)))

model = Sequential()
merged = Merge([model_chords, model_notes])
model.add(merged)
model.add(LSTM(20, stateful=True))
model.add(Dense(10000, activation='softmax'))

model.load_weights("NN_model.h5")
model.compile(optimizer='adam',loss='sparse_categorical_crossentropy',metrics=['accuracy'])
print(model.predict([np.array([1]), np.array([2.])], batch_size=1, verbose=1).argmax())

print("OK")


