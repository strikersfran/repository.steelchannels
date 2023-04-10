# -*- coding: utf-8 -*-
import sys
from resources.lib.utils import urlResolver
from resources.lib.loggers import showErrorNotification

class replacement_stderr(sys.stderr.__class__):
    def isatty(self): return False

sys.stderr.__class__ = replacement_stderr

# Get the plugin url in plugin:// notation.
__url__ = sys.argv[0]
# Get the plugin handle as an integer number.
__handle__ = int(sys.argv[1])

paramstring = sys.argv[2]
url = paramstring[1:]

if url:
    urlResolver(__handle__,url)
else:
    showErrorNotification("Debes enviar un url válido")