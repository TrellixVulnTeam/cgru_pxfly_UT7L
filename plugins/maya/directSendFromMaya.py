# This is for maya to direct send jobs to afanasy without keeper

import os
import sys

# Set CGRU root:
os.environ['CGRU_LOCATION'] = 'C:/cgru-windows'
os.environ['AF_ROOT'] = os.environ['CGRU_LOCATION'] + '/afanasy'

# Python module path:
os.environ['CGRU_PYTHON'] = os.environ['CGRU_LOCATION'] + '/lib/python'

# Python look path:
os.environ['PYTHONPATH'] = os.environ['CGRU_PYTHON'] + ';' + os.environ['PYTHONPATH']

# Python exe path:
os.environ['CGRU_PYTHONEXE'] = os.environ['CGRU_LOCATION'] + '/python/python.exe'

# Set CGRU Maya scripts location:
os.environ['MAYA_CGRU_LOCATION'] = os.environ['CGRU_LOCATION'] + '/plugins/maya'


# init afanasy script
sys.path.insert(0, os.environ['MAYA_CGRU_LOCATION'])
import afanasy
reload(afanasy)
afanasy.UI()