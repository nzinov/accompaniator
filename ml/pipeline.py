from base_mapper import MapperError

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
            stats.update(mapper.get_stats())
        return stats
