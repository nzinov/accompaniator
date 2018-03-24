from fetch import *
from mappers import *
from simplifier import *

corpus = SongCorpus()

# mappers
bsrm = BadSongsRemoveMapper()
nrm = NoiseReductionMapper()
tsm = TimeSignatureMapper()
uim = UnneededInstrumentsMapper()
ptfcm = PreToFinalConvertMapper()
# simplifier
mdm = MelodyDetectionMapper()
nuctrm = NonUniformChordsTracksRemoveMapper()
gssm = GetSongStatisticsMapper()

corpus.pipeline.mappers = [bsrm, nrm, tsm, uim, ptfcm, nuctrm, gssm]

corpus.apply_pipeline('raw.pickle', 'dataset.pickle')
