import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    pass


class MapperError(Exception):
    """Basic exception for handler"""

    def __init__(self, msg=None):
        if msg is None:
            msg = "Mapper failed to process song"
        super(MapperError, self).__init__(msg)


class BaseMapper:
    def __init__(self, prefix=None, n_examples=10):
        """
        :param prefix: The name of mapper which would be displayed (default is class name)
        :param n_examples: How many examples should be stored.
        """
        self.stats = dict()
        self.examples = dict()
        self.n_examples = n_examples

        if prefix is None:
            self.prefix = self.__class__.__name__
        else:
            self.prefix = prefix

    def add_example(self, name, value, examples_vault=None):
        if examples_vault is None:
            examples_vault = self.examples

        if name in examples_vault.keys():
            if len(examples_vault[name]) < self.n_examples:
                examples_vault[name].append(value)
        else:
            examples_vault[name] = [value]

    def increment_stat(self, name, stat_vault=None, count=1):
        if stat_vault is None:
            stat_vault = self.stats
        if name in stat_vault:
            stat_vault[name] += count
        else:
            stat_vault[name] = count

    def example_and_increment(self, song, name):
        self.increment_stat(name)
        self.add_example(name, song.name)

    def process(self, song):
        pass

    def get_stats(self):
        return {str((self.prefix, key)): self.stats[key] for key in self.stats.keys()}

    def get_examples(self):
        return {str((self.prefix, key)): self.examples[key] for key in self.examples.keys()}

    def plot_all_stat(self, many_items_border=15):
        stats = self.get_stats()

        def plot_with_style(df, ax, kind):
            df.plot(kind=kind, ax=ax, x='x', y='y', color=plt.get_cmap("tab10")(0))

        for name, stat in stats.items():
            if type(stat) == dict:
                if len(stat.items()) < many_items_border:
                    print(name, sorted(stat.items()))
                df = pd.DataFrame.from_records(sorted(stat.items()), columns=['x', 'y'])
                plt.figure(figsize=(10, 5))
                ax = plt.subplot(1, 2, 1)
                plot_with_style(df, ax, 'line')
                ax = plt.subplot(1, 2, 2)
                if len(stat.items()) < many_items_border:
                    plot_with_style(df, ax, 'bar')
                else:
                    plot_with_style(df, ax, 'hist')
                plt.title(name)
                plt.show()
            else:
                print(name, stat)
