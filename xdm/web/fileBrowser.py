
import os
import string
import cherrypy
import json
from xdm import logger

# this is for the drive letter code, it only works on windows
if os.name == 'nt':
    from ctypes import windll


# adapted from http://stackoverflow.com/questions/827371/is-there-a-way-to-list-all-the-available-drive-letters-in-python/827490
def getWinDrives():
    """ Return list of detected drives """
    assert os.name == 'nt'

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives() # @UndefinedVariable
    for letter in string.uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives


def foldersAtPath(path, includeParent=False, addFiles=False):
    """ Returns a list of dictionaries with the folders contained at the given path
        Give the empty string as the path to list the contents of the root path
        under Unix this means "/", on Windows this will be a list of drive letters)
    """
    assert os.path.isabs(path) or path == ""

    # walk up the tree until we find a valid path
    while path and not os.path.isdir(path):
        if path == os.path.dirname(path):
            path = ''
            break
        else:
            path = os.path.dirname(path)

    if path == "":
        if os.name == 'nt':
            entries = [{'current_path': 'Root'}]
            for letter in getWinDrives():
                letterPath = letter + ':\\'
                entries.append({'name': letterPath, 'path': letterPath, 'isPath': True})
            return entries
        else:
            path = '/'

    # fix up the path and find the parent
    path = os.path.abspath(os.path.normpath(path))
    parentPath = os.path.dirname(path)

    # if we're at the root then the next step is the meta-node showing our drive letters
    if path == parentPath and os.name == 'nt':
        parentPath = ""

    fileList = [{ 'name': filename, 'path': os.path.join(path, filename), 'isPath': os.path.isdir(os.path.join(path, filename)) } for filename in os.listdir(path)]
    fileList = sorted(fileList, lambda x, y: cmp(os.path.basename(x['name']).lower(), os.path.basename(y['path']).lower()))
    finalFileList = filter(lambda entry: entry['isPath'], fileList) # always add folders
    if addFiles:
        logger.log("adding files")
        finalFileList.extend(filter(lambda entry: not entry['isPath'], fileList)) # add files

    entries = [{'current_path': path}]
    if includeParent and parentPath != path:
        entries.append({ 'name': "..", 'path': parentPath, 'isPath': True})
    entries.extend(finalFileList)

    return entries


class WebFileBrowser:

    @cherrypy.expose
    def index(self, path='', showFiles="false"):
        cherrypy.response.headers['Content-Type'] = "application/json"
        showFiles = showFiles != "false"
        return json.dumps(foldersAtPath(path, True, showFiles))

    @cherrypy.expose
    def complete(self, term):
        cherrypy.response.headers['Content-Type'] = "application/json"
        paths = [entry['path'] for entry in foldersAtPath(os.path.dirname(term)) if 'path' in entry]
        return json.dumps(paths)
