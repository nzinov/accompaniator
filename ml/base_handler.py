class HandlerError(Exception):
    """Basic exception for handler"""
    def __init__(self, msg):
        if msg is None:
            msg = "Handler did not handle a song"
        super(HandlerError, self).__init__(msg)

class BaseHandler:
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

class MyHandler(BaseHandler):
    def process(self, song):
        self.log("len", len(song))
        if len(song) == 0:
            raise HandlerError("KOROTKOVATO")
            #return song
        else:
            return song + " :)"

class Pipeline:
    
    handlers = []
    instance = None
    
    def __init__(self, handlers):
        if not Pipeline.instance:
            Pipeline.instance = True
            self.handlers = handlers
        else:
            raise ValueError("Pipeline already exists")

    def midi_to_song(self, midi_name):
        pass

    def process(self, midi_name):
        #song = midi_to_song(midi_name)
        song = midi_name
        try:
            for handler in self.handlers:
                song = handler.process(song)
        except HandlerError:
            print("Something went wront with handler")
        return song

    def get_stats(self):
        stats = {}
        for handler in self.handlers:
            stats = {**stats, **handler.get_stats()}
        return stats
 
myhandler = MyHandler("cool_handler")

pipeline = Pipeline([myhandler])
print(pipeline)
print(pipeline.process("hi"))
print(pipeline.process(""))
print(pipeline.get_stats())
