from fetch import *
from mappers import *
from simplifier import *

corpus = SongCorpus()

bsrm = BadSongsRemoveMapper()
nrm = NoiseReductionMapper()
tsm = TimeSignatureMapper()
uim = UnneededInstrumentsMapper()
ptfcm = PreToFinalConvertMapper()
#mdm = MelodyDetectionMapper()
nutrm = NonUniformTracksRemoveMapper()
gssm = GetSongStatisticsMapper()

corpus.pipeline.mappers = [bsrm, nrm, tsm, uim, ptfcm, nutrm, gssm]

corpus.apply_pipeline('raw.pickle', 'dataset.pickle')
