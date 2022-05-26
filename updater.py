import requests as req
import subprocess, re, os, winreg

LAST_UPDATE = '64564048'
RLS_ID_PATTERN = r'[0-9]{8}'

API_ENDPOINT = 'https://api.github.com/repos/dio-gh/pcsx2/releases'

# ensure correct working dir
os.chdir(os.path.dirname(__file__))

# set up path to 7-Zip
reg_key = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'Software\7-Zip')
reg_val, regtype = winreg.QueryValueEx(reg_key, 'Path')
winreg.CloseKey(reg_key)
extractor = reg_val + "7z.exe"

# query the latest marked release
res = req.get(API_ENDPOINT, params={'per_page': '1'}).json()[0]

# when the release ID is not the same as the one stored locally, pull
if str(res["id"]) != LAST_UPDATE:

    assets = [next(filter(lambda x : 'AVX2-wxWidgets.7z' in x["name"], res["assets"])),
              next(filter(lambda x : 'AVX2-Qt.7z' in x["name"], res["assets"]))]

    for asset in assets:
        # retrieve the update archive
        update_blob = req.get(asset["browser_download_url"])
        update_fname = asset["name"]
        open(update_fname, 'wb').write(update_blob.content)

        # extract the update archive
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        extraction_proc = subprocess.Popen(
            [extractor, 'x', '-y', update_fname],
            startupinfo=si)
        extraction_status = extraction_proc.wait()

        # erase the update archive
        os.remove(update_fname)

    # on success, update the last update's ID based on the update's filename
    if extraction_status == 0:
        with open(os.path.basename(__file__), 'r+') as this_script:
            updated_script = re.sub(
                f"(LAST_UPDATE = )'{RLS_ID_PATTERN}'",
                f"\\1'{res['id']}'",
                this_script.read())
            this_script.seek(0)
            this_script.write(updated_script)
            this_script.truncate()
