from csv import reader
from pathlib import Path
from os import path, sep as pathseparator
from json import loads as jsonloads
from cryptography.fernet import Fernet
from pyInstalledPath import relpath
from serverCom import server_get, server_set

def nacistUdaje(file = relpath("resources/ucastnici.csv")) -> dict:
    with open(file, mode="r", encoding="utf-8") as attendee_file:
        attendee_list = list(reader(attendee_file, delimiter=";"))
    if len(attendee_list) > 0:
        attendee_list = attendee_list[1:]
    return {x[0]: x[1] for x in attendee_list}

attendee_dict = nacistUdaje()

FERNET_KEY = b'WXumKxmVEDCWtTNJ007L9d-0cSyfHKnf2vj_dpJ6EUQ='

fernet = Fernet(FERNET_KEY)

def overitPrihlaseni(username: str, password: str, attendee_dict: dict) -> bool:
    if username in attendee_dict.keys():
        if password == attendee_dict[username]:
            return True
    return False

nazevConfigSouboru = path.expanduser("~") + pathseparator + "user.u8"

def zkontrolovatConfigSoubor():
    return Path(nazevConfigSouboru).exists()

def nacistConfigSoubor():
    with open(nazevConfigSouboru, mode="rb") as saveFile:
        ulozenaData = jsonloads(str(fernet.decrypt(saveFile.read()), encoding="utf-8"))
    return ulozenaData

def ulozitConfigSoubor(data: dict):
    ulozenaDataStr = fernet.encrypt(bytes(str(data).replace("'", '"'), encoding="utf-8"))
    with open(nazevConfigSouboru, mode="wb") as saveFile:
        saveFile.write(ulozenaDataStr)

def vytvoritConfigSoubor(user: str, pwd: str):
    ulozenaData = {"username": user, "password": pwd, "hint": 0, "task": 0}
    ulozitConfigSoubor(ulozenaData)
    return ulozenaData

def synchrozovaniServeru(data: dict):
    serverGetStatus = server_get(data["username"])
    if serverGetStatus == -1:
        return False, data
    fromServer = [bool(serverGetStatus%2), bool(serverGetStatus//2)]
    toSend = [bool(serverGetStatus%2), bool(serverGetStatus//2)]
    
    if data["hint"] != fromServer[0]:
        if data["hint"]:
            toSend[0] = True
        else:
            data["hint"] = 1
    
    if data["task"] != fromServer[1]:
        if data["task"]:
            toSend[1] = True
        else:
            data["task"] = 1
    
    if fromServer != toSend:
        serverSetStatus = 0
        if toSend[0]:
            serverSetStatus += 1
        if toSend[1]:
            serverSetStatus += 2
        server_set(data["username"], serverSetStatus)
    
    ulozitConfigSoubor(data)
    return True, data
            
