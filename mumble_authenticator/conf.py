from collections import defaultdict


class Settings:
    _data = defaultdict()

    def from_ini(self, path):
        pass

    def __getattr__(self, key):
        try:
            return self._data[key]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self._data[key] = value


settings = Settings()
