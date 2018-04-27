from dataset.base_mapper import MapperError
import json
import pickle


# Can't encode keys in dictionary.
class ComplexEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            # print('default', type(o), o)
            return super().default(o)
        except TypeError:
            return '"' + str(o) + '"'

    def encode(self, o):
        try:
            # print('encode', type(o), o)
            return super().encode(o)
        except TypeError:
            return '"' + str(o) + '"'

    def iterencode(self, o, **kwargs):
        try:
            # print('iterencode', type(o), o)
            return super().iterencode(o)
        except TypeError:
            return '"' + str(o) + '"'


class Pipeline:
    mappers = []

    def __init__(self, mappers):
        self.mappers = mappers

    def process(self, songs):
        if type(songs) is not list:
            songs = [songs]
        for mapper in self.mappers:
            new_songs = []
            for song in songs:
                try:
                    song = mapper.process(song)
                except MapperError:
                    continue
                # except Exception as err:
                #     log.warning("Mapper %s failed: %s"%(mapper.prefix, str(err)))

                if type(song) is not list:
                    song = [song]
                new_songs += song
            songs = new_songs
        return songs

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

    def plot_all_stat(self, many_items_border=15):
        for mapper in self.mappers:
            mapper.plot_all_stat(many_items_border)

    def dump_stats(self, out_file):
        json.dump({'stats': self.get_stats(),
                   'examples': self.get_examples()},
                  out_file, sort_keys=True, indent=4,
                  default=str, cls=ComplexEncoder)

    def dump_pickle(self, out_file_name):
        with open(out_file_name, 'wb') as out_file:
            pickle.dump({'stats': self.get_stats(),
                         'examples': self.get_examples()},
                        out_file)
