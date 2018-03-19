class MapperError(Exception):
    """Basic exception for handler"""

    def __init__(self, msg):
        if msg is None:
            msg = "Mapper did not handle a song"
        super(MapperError, self).__init__(msg)


class BaseMapper:
    def __init__(self, prefix=None, n_examples=10):
        self.stats = dict()
        self.examples = dict()
        self.n_examples = n_examples

        if prefix is None:
            self.prefix = self.__class__.__name__
        else:
            self.prefix = prefix

    def add_stats(self, stat_names):
        for stat_name in stat_names:
            self.stats[stat_name] = 0
            self.examples[stat_name] = list()

    def add_example(self, name, value):
        if len(self.examples[name]) < self.n_examples:
            self.examples[name].append(value)

    def increment_counter(self, song, name):
        self.stats[name] += 1
        self.add_example(name, song.name)

    def process(self, song):
        pass

    def get_stats(self):
        return {str((self.prefix, key)): self.stats[key] for key in self.stats.keys()}

    def get_examples(self):
        return {str((self.prefix, key)): self.examples[key] for key in self.examples.keys()}
