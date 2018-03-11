from pipeline import Pipeline
from simplifier import NonUniformRemover

mappers = [NonUniformRemover("non-uniform")]

pipeline = Pipeline(mappers)

#process your songs here
