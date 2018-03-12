class MapperError(Exception):
    """Basic exception for handler"""

    def __init__(self, msg):
        if msg is None:
            msg = "Mapper did not handle a song"
        super(MapperError, self).__init__(msg)


class BaseMapper:
    def __init__(self, prefix=''):
        self.stats = {}
        self.prefix = prefix

    def process(self, song):
        pass

    def log(self, param, value):
        self.stats[param] = value

    def get_stats(self):
        return {(self.prefix, key): self.stats[key] for key in self.stats.keys()}
