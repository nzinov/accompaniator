from ml.dataset.mappers_preprocess import *
from ml.dataset.mappers_simplify import *
import sys

""" Usage: python main.py midi_dir """

midi_dir = sys.argv[1]
corpus = SongCorpus()

os.chdir(midi_dir)
corpus.process_parallel_from_directory('.')
os.system("cat */out.pickle > raw.pickle")

corpus.pipeline.mappers = \
    [
        # preprocess
        BadSongsRemoveMapper(),
        NoiseReductionMapper(),
        TimeSignatureMapper(),
        UnneededInstrumentsMapper(),
        PreToFinalConvertMapper(),
        # simplify
        MelodyDetectionMapper(strategy='most probable', fun=np.min, min_unique_notes=5),
        SplitNonMelodiesToGcdMapper(min_gcd=16),
        MergeTracksMapper(),
        AdequateCutOutLongChordsMapper(min_big_chord_duration=256, min_track_duration=10*128/4),
        GetSongStatisticsMapper()
    ]

corpus.apply_pipeline('raw.pickle', 'dataset.pickle')
