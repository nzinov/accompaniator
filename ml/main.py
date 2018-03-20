from fetch import *
from mappers import *

corpus = SongCorpus()

bsrm = BadSongsRemoveMapper()
nrm = NoiseReductionMapper()
tsm = TimeSignatureMapper()
uim = UnneededInstrumentsMapper()
ptfcm = PreToFinalConvertMapper()

corpus.pipeline.mappers = [bsrm, nrm, tsm, uim, ptfcm]

corpus.apply_pipeline('raw.pickle', 'dataset.pickle')
