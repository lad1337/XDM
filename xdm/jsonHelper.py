import json
import datetime
from time import mktime


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            #return int(mktime(obj.timetuple()))
            return '%s' % obj
        elif hasattr(obj, '__json__'):
            return obj.__json__()

        return json.JSONEncoder.default(self, obj)
