import matplotlib.pyplot as plt
import numpy as np

y = np.load("y.npy")
X = np.load("X.npy")
#els, counts = np.unique(y, return_counts=True)
#plt.scatter(range(len(els)), counts)
#plt.show()
#print(els)

print(X[0,:])
X_cat = X[:,8:16]
X_real = np.int_(np.hstack([X[:,:8], X[:,16:]]))

print(X_cat, X_real)

from sklearn.preprocessing import LabelEncoder

enc = LabelEncoder()
enc.fit(X_cat.reshape(X_cat.size))
print(enc.classes_)
for i in range(8):
    X_cat[:, i] = enc.transform(X_cat[:, i])

X = np.hstack([np.int_(X_cat), X_real])


from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y)

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score

clf = GradientBoostingClassifier()
clf.fit(X_train, y_train)

print(X_test)

print(accuracy_score(y_test, clf.predict(X_test)))

print(y_test[10], X_test[10,:], clf.predict(X_test)[10])
