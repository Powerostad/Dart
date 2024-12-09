class TradingAlgorithm:
    def __init__(self):
        pass

    def get_signal(self, df):
        raise NotImplementedError("Subclasses must implement the get_signal method.")