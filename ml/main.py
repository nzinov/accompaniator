from corpus import *
from mappers_preprocess import *
from mappers_simplify import *

corpus = SongCorpus()

# preprocess
bsrm = BadSongsRemoveMapper()
nrm = NoiseReductionMapper()
tsm = TimeSignatureMapper()
uim = UnneededInstrumentsMapper()
ptfcm = PreToFinalConvertMapper()

# simplify
colcm = CutOutLongChordsMapper(strategy='split', min_big_pause_duration=256)
mdm = MelodyDetectionMapper(strategy='most probable')

sctgm = SplitNonMelodiesToGcdMapper()
#nuctrm = NonUniformChordsTracksRemoveMapper()

mtm = MergeTracksMapper()
grm = GetResultMapper()
gssm = GetSongStatisticsMapper()

corpus.pipeline.mappers = [bsrm, nrm, tsm, uim, ptfcm,
                           colcm, mdm, sctgm, mtm, grm, gssm]

corpus.apply_pipeline('raw.pickle', 'dataset.pickle')
