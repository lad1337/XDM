# coding=UTF-8
"""
Usage:
    python setup.py
"""

from distutils.core import setup

import sys
import os
app_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_path)
sys.path.append(os.path.join(app_path, 'rootLibs'))

import re
import platform
import getopt
import shutil
import glob
from datetime import date
import subprocess
from subprocess import call, Popen
import urllib, ConfigParser
from distutils.core import setup
import zipfile, fnmatch
import git


######################
# helper functions
# ascii art done here http://www.network-science.de/ascii/
def fancyLogoMac():
    return r"""
__   _______  __  __    ____   _______   __
\ \ / /  __ \|  \/  |  / __ \ / ____\ \ / /
 \ V /| |  | | \  / | | |  | | (___  \ V / 
  > < | |  | | |\/| | | |  | |\___ \  > <  
 / . \| |__| | |  | | | |__| |____) |/ . \ 
/_/ \_\_____/|_|  |_|  \____/|_____//_/ \_\
"""


def fancyLogoWin():
    return r"""
__   _______  __  __  __          _______ _   _ 
\ \ / /  __ \|  \/  | \ \        / /_   _| \ | |
 \ V /| |  | | \  / |  \ \  /\  / /  | | |  \| |
  > < | |  | | |\/| |   \ \/  \/ /   | | | . ` |
 / . \| |__| | |  | |    \  /\  /   _| |_| |\  |
/_/ \_\_____/|_|  |_|     \/  \/   |_____|_| \_|
"""


def writeXDMVersionFile(major, minor, revision, build):
    from xdm import version

    content = 'major = %s\nminor = %s\nrevision = %s\nbuild = %s\n' % (major, minor, revision, build)
    # write
    writeXDMVersionFileRaw(content)
    reload(version)

    if version.major == major and\
        version.minor == minor and\
        version.revision == revision and\
        version.build == build:
        return True
    else:
        print "written and importent versions dont match!!!"
        return False


def writeXDMVersionFileRaw(content):
    # Create a file object:
    # in "write" mode
    versionFile = open(os.path.join("xdm", "version.py"), "w")
    versionFile.writelines(content)
    versionFile.close()


def readXDMVersionFile():
    versionFile = open(os.path.join("xdm", "version.py"), "r+")
    content = versionFile.read()
    versionFile.close()
    return content


def getNiceOSString(buildParams):
    if (sys.platform == 'darwin' and buildParams['target'] == 'auto') or buildParams['target'] in ('osx', 'OSX', 'MAC'):
        return "OSX"
    elif (sys.platform == 'win32' and buildParams['target'] == 'auto')  or buildParams['target'] in ('win', 'WIN', 'Win32'):
        return "Win"
    else:
        return "unknown"


def getLatestCommitID(buildParams):
    repo = git.Repo('./')                   # get the local repo
    local_commit = repo.commit()                    # latest local commit

    longID = local_commit.hexsha
    shortID = longID[:6]
    return (longID, shortID)


def getBranch(buildParams):
    branchRaw = subprocess.Popen(["git", "branch"], stdout=subprocess.PIPE).communicate()[0]

    regex = "(\* (\w+))"
    match = re.search(regex, branchRaw)
    if match:
        return match.group(2)
    else:
        return "unknown"


def writeChangelog(buildParams):
    # start building the CHANGELOG.txt
    print 'Creating / writing changelog'
    gh = github.GitHub()
    lastCommit = ""
    changeString = ""

    # cycle through all the git commits and save their commit messages
    for curCommit in gh.commits('lad1337', 'Sick-Beard', buildParams['currentBranch']):
        if curCommit['sha'] == lastCommit:
            break
        curID = curCommit['sha']
        changeString += "#### %s (%s) ####\n%s\n############################################\n\n" % (curID[:6], curCommit['commit']['committer']['date'], curCommit['commit']['message'])

    # if we didn't find any changes don't make a changelog file
    if buildParams['gitNewestCommit'] != "":
        newChangelog = open(os.path.join('dist', "CHANGELOG.txt"), "w")
        newChangelog.write("Changelog for build " + str(buildParams['build']) + " (" + buildParams['gitNewestCommit'] + ")\n\n")
        newChangelog.write(changeString)
        newChangelog.close()
        print "changelog writen"
    else:
        print "No changes found, keeping old changelog"


def recursive_find_data_files(root_dir, allowed_extensions=('*')):
    to_return = {}
    for (dirpath, dirnames, filenames) in os.walk(root_dir):
        if not filenames:
            continue
        for cur_filename in filenames:
            matches_pattern = False
            for cur_pattern in allowed_extensions:
                if fnmatch.fnmatch(cur_filename, '*.' + cur_pattern):
                    matches_pattern = True
            if not matches_pattern:
                continue
            cur_filepath = os.path.join(dirpath, cur_filename)
            to_return.setdefault(dirpath, []).append(cur_filepath)

    return sorted(to_return.items())


def find_all_libraries(root_dirs):
    libs = []
    for cur_root_dir in root_dirs:
        for (dirpath, dirnames, filenames) in os.walk(cur_root_dir):
            if '__init__.py' not in filenames:
                continue
            libs.append(dirpath.replace(os.sep, '.'))

    return libs


def allFiles(dir):
    files = []
    for file in os.listdir(dir):
        fullFile = os.path.join(dir, file)
        if os.path.isdir(fullFile):
            files += allFiles(fullFile)
        else:
            files.append(fullFile)

    return files


#####################
#  build functions  #
#####################
def buildWIN(buildParams):
    #constants
    Win32ConsoleName = 'XDM-console.exe'
    Win32WindowName = 'XDM.exe'

    try:
        import py2exe
    except ImportError:
        print
        print 'ERROR you need py2exe to build a win binary http://www.py2exe.org/'
        return False

    # save the original arguments and replace them with the py2exe args
    oldArgs = []
    if len(sys.argv) > 1:
        oldArgs = sys.argv[1:]
        del sys.argv[1:]

    sys.argv.append('py2exe')

    # set up the compilation options
    data_files = recursive_find_data_files('data', ['gif', 'png', 'jpg', 'ico', 'js', 'css', 'tmpl'])

    options = dict(
        name=buildParams['name'],
        version=buildParams['build'],
        author='%s-Team' % buildParams['name'],
        author_email='lad1337@gmail.com',
        description=buildParams['packageName'],
        scripts=[buildParams['mainPy']],
        packages=find_all_libraries(['sickbeard', 'lib']),
    )

    # set up py2exe to generate the console app
    program = [ {'script': buildParams['mainPy'] } ]
    options['options'] = {'py2exe':
                            {
                             'bundle_files': 3,
                             'packages': ['Cheetah'],
                             'excludes': ['Tkconstants', 'Tkinter', 'tcl'],
                             'optimize': 2,
                             'compressed': 0
                            }
                         }
    options['zipfile'] = 'lib/sickbeard.zip'
    options['console'] = program
    options['data_files'] = data_files

    if buildParams['test']:
        print
        print "########################################"
        print "NOT Building exe this was a TEST."
        print "########################################"
        return True

    # compile sickbeard-console.exe
    setup(**options)

    # rename the exe to sickbeard-console.exe
    try:
        if os.path.exists("dist/%s" % Win32ConsoleName):
            os.remove("dist/%s" % Win32ConsoleName)
        os.rename("dist/%s" % Win32WindowName, "dist/%s" % Win32ConsoleName)
    except:
        print
        print "########################################"
        print "Cannot create dist/%s" % Win32ConsoleName
        print "########################################"
        return False

    # we don't need this stuff when we make the 2nd exe
    del options['console']
    del options['data_files']
    options['windows'] = program

    # compile sickbeard.exe
    setup(**options)

    # compile sabToXDM.exe using the existing setup.py script

    auto_process_dir = 'autoProcessTV'
    p = subprocess.Popen([ sys.executable, 'setup.py' ], cwd=auto_process_dir)
    o, e = p.communicate()
    # copy autoProcessTV files to the dist dir
    auto_process_files = ['autoProcessTV/sabToXDM.py',
                          'autoProcessTV/hellaToXDM.py',
                          'autoProcessTV/autoProcessTV.py',
                          'autoProcessTV/autoProcessTV.cfg.sample',
                          'autoProcessTV/sabToXDM.exe']

    os.makedirs('dist/autoProcessTV')

    print
    print "########################################"
    print "Copy Files"
    print "########################################"
    for curFile in auto_process_files:
        newFile = os.path.join('dist', curFile)
        print "Copying file from", curFile, "to", newFile
        shutil.copy(curFile, newFile)

    # compile updater.exe
    setup(
          options={'py2exe': {'bundle_files': 1}},
          zipfile=None,
          console=['updater.py'],
    )

    print
    print "########################################"
    print 'Zipping files...'
    print "########################################"
    zipFilename = os.path.join('dist', buildParams['packageName'])

    # get a list of files to add to the zip
    zipFileList = allFiles('dist')
    # add all files to the zip
    z = zipfile.ZipFile(zipFilename + '.zip', 'w', zipfile.ZIP_DEFLATED)
    for file in zipFileList:
        z.write(file, file.replace('dist', buildParams['packageName']))
    z.close()

    print
    print "########################################"
    print "EXE build successful."
    print "ZIP is located at %s" % os.path.abspath(zipFilename)
    print "########################################"
    return True


def buildOSX(buildParams):
    # OSX constants
    bundleIdentifier = "de.lad1337.xdm" # unique program identifier
    osxOriginalSpraseImageZip = "Meta-Resources/template.xdm.sparseimage.zip" # 
    osxSpraseImage = "build/template.xdm.sparseimage"
    osxAppIcon = "Meta-Resources/xdm-icon.icns" # the app icon location
    osVersion = platform.mac_ver()[0]
    osxDmg = "dist/%s.dmg" % buildParams['packageName'] # dmg file name/path

    try:
        import PyObjCTools
    except ImportError:
        print
        print "########################################"
        print 'WARNING PyObjCTools is not available'
        print 'this is included in the default python that comes with the system'
        print 'you can try: sudo easy_install pyobjc==2.2'
        print 'however the app can be build but the mac menu will be missing !!'
        print "########################################"

    try:
        import py2app
    except ImportError:
        print
        print 'ERROR you need py2app to build a mac app http://pypi.python.org/pypi/py2app/'
        return False

    #XDM-win32-alpha-build489.zip
    # Check which Python flavour
    apple_py = 'ActiveState' not in sys.copyright

    APP = [buildParams['mainPy']]
    DATA_FILES = ['html',
                  'xdm',
                  'lib',
                  'rootLibs',
                  'corePlugins',
                  'i18n']
    _NSHumanReadableCopyright = "(c) %s Dennis Lutter\nBuild on: %s %s\nBased on: %s\nPython used & incl: %s" % (buildParams['thisYearString'],
                                                                                                                    buildParams['osName'],
                                                                                                                    osVersion,
                                                                                                                    buildParams['gitNewestCommit'],
                                                                                                                    str(sys.version))

    OPTIONS = {'argv_emulation': False,
               'iconfile': osxAppIcon,
               'packages':["xml", "OpenSSL"],
               'plist': {'NSUIElement': 1,
                        'CFBundleShortVersionString': buildParams['build'],
                        'NSHumanReadableCopyright': _NSHumanReadableCopyright,
                        'CFBundleIdentifier': bundleIdentifier,
                        'CFBundleVersion': buildParams['build']
                        }
               }
    if len(sys.argv) > 1:
        sys.argv = [sys.argv[1]]
    for x in buildParams['py2AppArgs']:
        sys.argv.append(x)

    if buildParams['test']:
        print
        print "########################################"
        print "NOT Building App this was a TEST. Here are the names"
        print "########################################"
        print "volumeName: " + buildParams['packageName']
        print "osxDmg: " + osxDmg
        print "OPTIONS: " + str(OPTIONS)
        return True

    print
    print "########################################"
    print "Building App"
    print "########################################"
    setup(
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
        )
    if buildParams['onlyApp']:
        print
        print "########################################"
        print "STOPING here you only wanted the App"
        print "########################################"
        return True

    print
    print "########################################"
    print "Build finished. Creating DMG"
    print "########################################"
    # unzip template sparse image
    call(["unzip", osxOriginalSpraseImageZip, "-d", "build"])

    # mount sparseimage and modify volumeName label
    os.system("hdiutil mount %s | grep /Volumes/XDM >build/mount.log" % (osxSpraseImage))

    # Select OSX version specific background image
    # Take care to preserve the special attributes of the background image file
    if buildParams['osxDmgImage']:
        if os.path.isfile(buildParams['osxDmgImage']):
            print "Writing new background image. %s ..." % os.path.abspath(buildParams['osxDmgImage']),
            # we need to read and write the data because otherwise we would lose the special hidden flag on the file
            f = open(buildParams['osxDmgImage'], 'rb')
            png = f.read()
            f.close()
            f = open('/Volumes/XDM/sb_osx.png', 'wb')
            f.write(png)
            f.close()
            print "ok"
        else:
            print "The provided image path is not a file"
    else:
        print "# Using default background image"

    # Rename the volumeName
    fp = open('build/mount.log', 'r')
    data = fp.read()
    fp.close()
    m = re.search(r'/dev/(\w+)\s+', data)
    print "Renaming the volume ...",
    if not call(["disktool", "-n", m.group(1), buildParams['packageName']], stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        print "ok"
    else:
        print "ERROR"
        return False

    #copy builded app to mounted sparseimage
    print "Copying XDM.app ...",
    if not call(["cp", "-r", "dist/XDM.app", "/Volumes/%s/" % buildParams['packageName']], stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        print "ok"
    else:
        print "ERROR"
        return False

    print "# Sleeping 10 sec"
    os.system("sleep 10")
    #Unmount sparseimage
    print "Unmount sparseimage ...",
    if not call(["hdiutil", "eject", "/Volumes/%s/" % buildParams['packageName']], stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        print "ok"
    else:
        print "ERROR"
        return False

    #Convert sparseimage to read only compressed dmg
    print "Convert sparseimage to read only compressed dmg ...",
    if not call(["hdiutil", "convert", osxSpraseImage, "-format", "UDBZ", "-o", osxDmg], stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        print "ok"
    else:
        print "ERROR"
        return False

    #Make image internet-enabled
    print "Make image internet-enabled ...",
    if not call(["hdiutil", "internet-enable", osxDmg], stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        print "ok"
    else:
        print "ERROR"
        return False

    print
    print "########################################"
    print "App build successful."
    print "DMG is located at %s" % os.path.abspath(osxDmg)
    print "########################################"
    return True


def main():
    print
    print "########################################"
    print "Starting build ..."
    print "########################################"

    buildParams = {}
    ######################
    # check arguments
    # defaults
    buildParams['test'] = False
    buildParams['target'] = 'auto'
    buildParams['nightly'] = False
    buildParams['major'] = ""
    buildParams['minor'] = ""
    buildParams['revision'] = ""
    buildParams['branch'] = ""
    # win
    buildParams['py2ExeArgs'] = [] # not used yet
    # osx
    buildParams['onlyApp'] = False
    buildParams['py2AppArgs'] = ['py2app']
    buildParams['osxDmgImage'] = ""
    buildParams['buildNumber'] = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [ 'test', 'onlyApp', 'nightly', 'dmgbg=', 'py2appArgs=', 'target=', 'major=', 'minor=', 'revision=', 'branch=', 'buildNumber=']) #@UnusedVariable
    except getopt.GetoptError:
        print "Available options: --test, --dmgbg, --onlyApp, --nightly, --py2appArgs, --target, --major, --minor, --revision, --branch, --buildNumber"
        exit(1)

    for o, a in opts:
        if o in ('--test'):
            buildParams['test'] = True

        if o in ('--nightly'):
            buildParams['nightly'] = True

        if o in ('--dmgbg'):
            buildParams['osxDmgImage'] = a

        if o in ('--onlyApp'):
            buildParams['onlyApp'] = True

        if o in ('--py2appArgs'):
            buildParams['py2AppArgs'] = py2AppArgs + a.split()

        if o in ('--dmgbg'):
            buildParams['osxDmgImage'] = a

        if o in ('--target'):
            buildParams['target'] = a

        if o in ('--major'):
            buildParams['major'] = int(a)

        if o in ('--minor'):
            buildParams['minor'] = int(a)

        if o in ('--revision'):
            buildParams['revision'] = int(a)

        if o in ('--branch'):
            buildParams['branch'] = a

        if o in ('--buildNumber'):
            buildParams['buildNumber'] = int(a)

    ######################
    # constants
    buildParams['mainPy'] = "XDM.py" # this should never change
    buildParams['name'] = "XDM" # this should never change
    buildParams['majorVersion'] = "BETA" # one day we will change that to BETA :P

    buildParams['osName'] = getNiceOSString(buildParams)# look in getNiceOSString() for default os nice names

    """
    # maybe some day the git tag is used this might be handy although it might be easier ti use the github lib
    # dynamic build number and date stuff
    tagsRaw = subprocess.Popen(["git", "tag"], stdout=subprocess.PIPE).communicate()[0]
    lastTagRaw = tagsRaw.split("\n")[-2] # current tag e.g. build-###
    tag = lastTagRaw.split("-")[1] # current tag pretty... change according to tag scheme
    """
    # date stuff
    buildParams['thisYearString'] = date.today().strftime("%Y") # for the copyright notice

    buildParams['gitNewestCommit'], buildParams['gitNewestCommitShort'] = getLatestCommitID(buildParams)
    if not buildParams['branch']:
        buildParams['branch'] = getBranch(buildParams)
        buildParams['currentBranch'] = buildParams['branch']
    else:
        buildParams['currentBranch'] = getBranch(buildParams)

    from xdm import common
    current_major, current_minor, current_revision, current_build = common.getVersionTuple()

    if not buildParams['major']:
        buildParams['major'] = current_major
    if not buildParams['minor']:
        buildParams['minor'] = current_minor
    if not buildParams['revision']:
        buildParams['revision'] = current_revision
    if not buildParams['buildNumber']:
        buildParams['buildNumber'] = current_build

    OLD_VERSION_CONTENT = None
    if buildParams['buildNumber']:
        print "we got a build number", buildParams['buildNumber']
        # save old version.py
        OLD_VERSION_CONTENT = readXDMVersionFile()
        # write new version.py
        if not writeXDMVersionFile(buildParams['major'], buildParams['minor'], buildParams['revision'], buildParams['buildNumber']):
            print 'error while writing the new version file'
            exit(1)
        print readXDMVersionFile()

    # this is the 'branch yy.mm(.dd)' string
    buildParams['build'] = "%s %s" % (buildParams['branch'], common.getVersionHuman())
    # or for nightlys yy.mm.commit
    if buildParams['nightly']:
        buildParams['build'] = "%s.%s" % (buildParams['dateVersion'], buildParams['gitNewestCommitShort'])

    buildParams['packageName'] = "%s-%s-%s" % (buildParams['name'] , buildParams['osName'] , buildParams['build']) # volume name
    buildParams['packageName'] = buildParams['packageName'].replace(" ", "-")
    #####################
    # clean the build dirs
    scriptBuild = None
    scriptDist = None
    if not buildParams['test']:
        print "Removing old build dirs ...",
        # remove old build stuff
        if os.path.exists('build'):
            shutil.rmtree('build')
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        # a windows build creats these folder too ... clear them
        scriptBuild = os.path.join('autoProcessTV', 'build')
        scriptDist = os.path.join('autoProcessTV', 'dist')
        if os.path.exists(scriptBuild):
            shutil.rmtree(scriptBuild)
        if os.path.exists(scriptDist):
            shutil.rmtree(scriptDist)
        # create build dirs acctualy only the dist has to be made manual because the changelog will be writen there
        os.makedirs('build') # create tmp build dir
        os.makedirs('dist') # create tmp build dir
        # TODO: do some real testing and dont just say ok
        print "ok"
    #####################
    # write changelog
    #writeChangelog(buildParams)

    curFancyLogo = ""

    # os switch
    if buildParams['osName'] == 'OSX':
        result = buildOSX(buildParams)
        curFancyLogo = fancyLogoMac()
    elif buildParams['osName'] == 'Win':
        result = buildWIN(buildParams)
        curFancyLogo = fancyLogoWin()
    else:
        print "unknown os/target valid: OSX, Win"
        result = False

    if result:
        # reset version file
        if OLD_VERSION_CONTENT is not None:
            print
            print "########################################"
            print "Rewriting the old version file"
            print "########################################"
            writeXDMVersionFileRaw(OLD_VERSION_CONTENT)

        # remove the temp build dirs
        if os.path.exists('build'):
            shutil.rmtree('build')
        if scriptBuild and os.path.exists(scriptBuild):
            shutil.rmtree(scriptBuild)
        print curFancyLogo
        print
        print "########################################"
        print "Build SUCCESSFUL !!"
        print "########################################"
        exit()
    else:
        print
        print "########################################"
        print "ERROR during build ... i have failed you"
        print "########################################"
        exit(1)

if __name__ == '__main__':
    main()
