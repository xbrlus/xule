from collections import OrderedDict
from collections.abc import MutableMapping

from .XuleValue import XuleValue, XuleValueSet

class XuleCache(MutableMapping):
    def __init__(self, max_size_bytes):
        self.max_size_bytes = max_size_bytes
        self.values = OrderedDict()
        self.sizes = {}
        self.size = 0

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def __contains__(self, key):
        return key in self.values

    def __delitem__(self, key):
        self.size -= self.sizes.pop(key)
        del self.values[key]

    def __getitem__(self, key):
        self.values.move_to_end(key)
        return self.values[key]

    def __setitem__(self, key, value):
        self.size -= self.sizes.get(key, 0)
        self.values[key] = value
        self.sizes[key] = size = self._size(key, value)
        self.size += size
        while self.size > self.max_size_bytes:
            key, _ = self.values.popitem(last=False)
            self.size -= self.sizes.pop(key)

    def get(self, key, default=None):
        return self.values.get(key, default)

    @staticmethod
    def _size(key, value):
        # Assume 1 KB per XuleValue.
        xule_value_size = 1000
        default_size = 24
        try:
            key_size = sum(xule_value_size if isinstance(k, XuleValue) else default_size for k in key)
        except:
            key_size = default_size
        if isinstance(value, XuleValueSet):
            # Assume 200 B per XuleValueSet key.
            value_size = (200 + xule_value_size) * len(value.values)
        else:
            value_size = default_size
        return key_size + value_size
