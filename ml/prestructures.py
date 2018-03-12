class PreNote:
    """ Stores individual note
    Attributes:
        number: MIDI number of note
        velocity: MIDI velocity
        duration: duration in 1/128th notes
    """

    def __init__(self, number, duration, velocity):
        self.number = number
        self.velocity = velocity
        self.duration = duration

    def freq(self):
        """ Returns frequency in Hz """
        return 2**((self.number - 69)/12.)*440

    def __str__(self):
        return "%s %s %s"%(self.number, self.duration, self.velocity)

    def __repr__(self):
        return self.__str__()


class PreChord:
    """Stores a chord and its length in 1/128 beats"""

    def __init__(self, delta, notes_list):
        self.notes = notes_list[:]
        self.delta = delta

    def __str__(self):
        return "{%s %s}"%(self.delta, str(self.notes))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.notes == other.notes and self.delta == other.delta
