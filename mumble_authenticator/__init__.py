import os
import Ice


Ice.loadSlice('', [
    '-I' + Ice.getSliceDir(),
    os.path.join(os.path.dirname(__file__), 'Murmur.ice')
])
import Murmur
