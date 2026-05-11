# pip install lxml[html_clean]
# pip install requests-html
import requests
from requests_html import HTMLSession
import json
import shutil
import os
from os.path import expanduser

session = HTMLSession()
homedir = expanduser("~")

def download(link, path):
    r = session.get(link)

    if not os.path.exists(rf"{path}"):
        os.makedirs(rf"{path}")

    countracks = r.html.find('tr.track_row_view > td.title-col') 

    if countracks:
        for x in countracks:
            savetrack(x.absolute_links.pop(), path)
    else:
        savetrack(link, path)
    

def savetrack(link, path):
    r = session.get(link)
    for x in r.html.find('meta'):
        if 'title' in str(x):
            track, band = x.attrs['content'].split(', by ')
            break
    for x in r.html.find('script'):
        if 'stream' in str(x): 
            data_tralbum = dict(x.attrs).get('data-tralbum')
            url = json.loads(data_tralbum).get('trackinfo')[0].get('file').get('mp3-128')
            pathfile = rf'{path}/{band}-{track}.mp3'

            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(pathfile, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            print(url,band,track,'finish')