from base_mapper import MapperError
import json


class Pipeline:
    mappers = []

    def __init__(self, mappers):
        self.mappers = mappers

    def process(self, song):
        for mapper in self.mappers:
            try:
                song = mapper.process(song)
            except MapperError:
                return None
            # except Exception as err:
            #     print("Mapper %s failed: %s"%(mapper.prefix, str(err)))
            # TODO: раскомментить в продакшене.
        return song

    def get_stats(self):
        stats = {}
        for mapper in self.mappers:
            stats.update(mapper.get_stats())
        return stats

    def get_examples(self):
        examples = {}
        for mapper in self.mappers:
            examples.update(mapper.get_examples())
        return examples

    def dump_stats(self, outf):
        json.dump({'stats': self.get_stats(), 'examples': self.get_examples()}, outf)
