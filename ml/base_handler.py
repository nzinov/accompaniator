class MapperError(Exception):
    """Basic exception for handler"""
    def __init__(self, msg):
        if msg is None:
            msg = "Mapper did not handle a song"
        super(MapperError, self).__init__(msg)

class BaseMapper:
    def __init__(self, prefix):
        self.stats = {}
        self.prefix = prefix

    def process(self, song):
        pass

    def log(self, param, value):
        self.stats[param] = value

    def get_stats(self):
        return {self.prefix + ": " + key: self.stats[key] for key in self.stats.keys()}

    prefix = ""
    stats = {}

class MyMapper(BaseMapper):
    def process(self, song):
        self.log("len", len(song))
        if len(song) == 0:
            raise MapperError("KOROTKOVATO")
            #return song
        else:
            return song + " :)"

class Pipeline:
    
    mappers = []
    instance = None
    
    def __init__(self, mappers):
        if not Pipeline.instance:
            Pipeline.instance = True
            self.mappers = mappers
        else:
            raise ValueError("Pipeline already exists")

    def midi_to_song(self, midi_name):
        pass

    def process(self, midi_name):
        #song = midi_to_song(midi_name)
        song = midi_name
        try:
            for mapper in self.mappers:
                song = mapper.process(song)
        except MapperError as err:
            print("Something went wront with handler:" + str(err))
        return song

    def get_stats(self):
        stats = {}
        for mapper in self.mappers:
            stats = {**stats, **mapper.get_stats()}
        return stats
 
myhandler = MyMapper("cool_handler")

pipeline = Pipeline([myhandler])
print(pipeline)
print(pipeline.process("hi"))
print(pipeline.process(""))
print(pipeline.get_stats())
