# -*- coding: utf-8 -*-
import json
import os
from os.path import isfile

import googleapiclient.discovery
import youtube_dl

STORAGE_FILE = "data.json"
RESOURCE_FILE = "../resource.json"
SOUNDS_FILE = "../sounds.json"
SAVE_DIR = "../assets"

YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': '../assets/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',

    }],
    # 'progress_hooks': [progress_hook],
}


def fetch_info():
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = os.environ["YOUTUBE_API_KEY"]
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)
    request = youtube.search().list(
        part="snippet",
        channelId="UCyGVVmbXFDaIpILSOdxKPmg",
        maxResults=100,
        order="date"
    )
    response = request.execute()
    return response


def parse_new_info(info):
    ret = {}
    for i in info:
        if i['id']['kind'] != 'youtube#video':
            continue
        videoId = i['id']['videoId']
        publishTime = i['snippet']['publishedAt']
        title = i['snippet']['title']
        ret[videoId] = {
            "publishTime": publishTime,
            "title": title
        }
    return ret


def progress_hook(c):
    print("Downloading {} ({})", c['_percent_str'], c['_speed_str'])


def write_new_clip(vid, title):
    with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
        ydl.download(['https://www.youtube.com/watch?v={}'.format(vid)])


def main():
    if isfile(STORAGE_FILE):
        print("Picking {} as the source.".format(STORAGE_FILE))
        new_info = json.load(open(STORAGE_FILE))
    else:
        print("Fetching metadata from YouTube API.")
        new_info = parse_new_info(fetch_info().get('items'))
        print("Fetched. Saving to {}.".format(STORAGE_FILE))
        text = json.dumps(new_info, ensure_ascii=False)
        with open(STORAGE_FILE, 'w') as fs:
            fs.write(text)
        print("Saved to {}. Let's get started.".format(STORAGE_FILE))
    old_info = json.load(open(RESOURCE_FILE))
    sounds_info = json.load(open(SOUNDS_FILE))
    update_list = {}
    for [videoId, info] in new_info.items():
        if (videoId not in old_info) or (old_info[videoId]['publishTime'] != info['publishTime']):
            print("New clip:" if videoId not in old_info else 'Update clip:',
                  videoId, info['title'])
            write_new_clip(videoId, info['title'])
            old_info[videoId] = info
            # Save progress
            sounds_info.append({
                "name": info['title'],
                "file": "{}.mp3".format(videoId),
                "type": "normal",
                "metadata": {
                    "site": "youtube",
                    "identifier": videoId
                }
            })
            with open(RESOURCE_FILE, 'w') as fs:
                fs.write(json.dumps(old_info, ensure_ascii=False))
            with open(SOUNDS_FILE, 'w') as fs:
                fs.write(json.dumps(sounds_info, ensure_ascii=False))
            update_list[videoId] = info


if __name__ == "__main__":
    main()
