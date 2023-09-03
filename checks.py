import os
from typing import Union
from config import ALLOWED_ACCOUNTS
import subprocess

def is_allowed(username) -> Union[dict, bool]:
    for account in ALLOWED_ACCOUNTS:
        if account["email"] == username:
            return account

    return False

def avscan(path: str) -> tuple[bool, str]:
    if not os.path.exists(path):
        raise FileNotFoundError(path + "was not found")
    
    proc = subprocess.Popen(['clamdscan', '-m', '--fdpass', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = proc.communicate()

    # passed
    if str(out).find('FOUND') == -1:
        return True, ""

    # failed
    return False, out
