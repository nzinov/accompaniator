import matplotlib.pyplot as plt
import numpy as np
import pickle

y = np.load("y.npy")
X = (np.load("X.npy"))
print(X[0,:])
els, counts = np.unique(y, return_counts=True)
#plt.scatter(range(len(els)), counts)
#plt.show()
#print(els, counts)
rare = els[counts < 10]

isin = np.logical_not(np.isin(y, rare))
print(X.shape)
X = X[isin, :]
print(X.shape)
y = y[isin]

els, counts = np.unique(y, return_counts=True)
#plt.scatter(range(len(els)), counts)
#plt.show()
print(els)
print(len(els))


feat = X.shape[1]
print("Features:", feat)
tst = np.array([1])
tst1 = np.array([1.0])
print(tst.dtype, X.dtype)
print(X[0, 10])
print(X)
if X.dtype == tst.dtype or X.dtype == tst1.dtype:
    num_features = np.zeros(feat, dtype='bool')
else:
    num_features = np.array(['0' <= X[0, i] <= '9' for i in range(feat)])
cat_features = np.logical_not(num_features)


#X_cat = X[:,8:16]
#X_real = np.int_(np.hstack([X[:,:8], X[:,16:]]))

X_cat = X[:,cat_features]
X_real = np.int_(X[:,num_features])
print(X_cat[0,:])
print(X_real[0,:])

from sklearn.preprocessing import LabelEncoder

enc = LabelEncoder()
enc.fit(X_cat.reshape(X_cat.size))
for i in range(sum(cat_features)):
    print(enc.classes_)
for i in range(8):
    X_cat[:, i] = enc.transform(X_cat[:, i])

X = np.hstack([np.int_(X_cat), X_real])

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y)

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import custom_scorers
from sklearn.metrics import make_scorer

clf = RandomForestClassifier(n_estimators=20)
clf.fit(X_train, y_train)

print(X_test)

abs_dist_score = make_scorer(custom_scorers.chords_dist_error)
y_pred = clf.predict(X_test)
print(accuracy_score(y_test, y_pred)) 
print(abs_dist_score(clf, X_test, y_test))

with open('rf_nottingham.pkl', 'wb') as fid:
    pickle.dump(clf, fid)  
print(y_test[10], X_test[10,:], clf.predict(X_test)[10])
