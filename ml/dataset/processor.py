from ml.dataset.base_processor import BaseProcessor
import numpy as np

from ml.dataset.corpus import get_progressbar


class ForestProcessor(BaseProcessor):
    @staticmethod
    def cut_song2(song, num_tacts, l_min_note, delay=4):  # 3 arrays: notes, chords, beat
        l_piece = num_tacts * l_min_note
        # print('l_piece', l_piece)
        notes = np.array(song[0])
        chords = np.array(song[1])
        n = len(song[0])
        # print('n', n, len(song[1]))
        n_items = n // l_piece - 1
        # print('n_items', n_items)
        # print('n_items*l_piece', n_items*l_piece)
        X_notes = notes[:n_items * l_piece].reshape((n_items, l_piece))[:, :-delay]
        X_chords = chords[:n_items * l_piece].reshape((n_items, l_piece))[:, :-delay]

        X = np.hstack([X_notes, X_chords])
        y = np.array([chords[l_piece * (i + 1) + 1] for i in range(n_items)])
        return X, y

    def process(self, songs):
        n_tacts = 2
        X, y = np.ndarray(shape=(0, 56)), []
        for song in get_progressbar(songs):
            #     try:
            if len(song[0]) > 32:
                X_, y_ = ForestProcessor.cut_song2(song, n_tacts, 16, with_chords=True)
                X = np.vstack([X, X_])
                y = np.hstack([y, y_])
        #     except ValueError as e:
        #         print("Something wrong:", e)
        #         #print(song)
        return X, y
