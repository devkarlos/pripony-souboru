from os import path as ospath, sep as pathseparator
import sys

#určí relativní cestu, nezbytné pro pyinstaller
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = sys._MEIPASS
else:
    APPLICATION_PATH = ospath.dirname(ospath.abspath(__file__))

#funkce pro převedení relativní cesty na cestu pro pyinstaller
def relpath(path: str, application_path=APPLICATION_PATH) -> str:
    return application_path + pathseparator + path.replace("/", pathseparator)