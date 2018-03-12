from base_mapper import MapperError


class Pipeline:
    mappers = []

    def __init__(self, mappers):
        self.mappers = mappers

    def process(self, song):
        try:
            for mapper in self.mappers:
                song = mapper.process(song)
        except MapperError as err:
            print("Something went wrong with handler:" + str(err))
            return None
        return song

    def get_stats(self):
        stats = {}
        for mapper in self.mappers:
            stats.update(mapper.get_stats())
        return stats
