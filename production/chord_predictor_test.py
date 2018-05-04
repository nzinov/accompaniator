from chord_predictor import *

predictor = ChordPredictor()
predictor.load_model("rf_nottingham.pkl")

# создаём список аккордов

chords_list = []
for i in range(28):
    chords_list.append(Chord([Note(60)], 8, 1))

print(predictor.predict(chords_list))
