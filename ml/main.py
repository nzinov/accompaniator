from corpus import *
from mappers_preprocess import *
from mappers_simplify import *

corpus = SongCorpus()

corpus.pipeline.mappers = \
    [
        # preprocess
        BadSongsRemoveMapper(),
        NoiseReductionMapper(),
        TimeSignatureMapper(),
        UnneededInstrumentsMapper(),
        PreToFinalConvertMapper(),
        # simplify
        CutOutLongChordsMapper(strategy='split', min_big_pause_duration=256),
        MelodyDetectionMapper(strategy='most probable'),
        SplitNonMelodiesToGcdMapper(),  # or NonUniformChordsTracksRemoveMapper()
        MergeTracksMapper(),
        GetResultMapper(),
        GetSongStatisticsMapper()
    ]

corpus.apply_pipeline('raw.pickle', 'dataset.pickle')
