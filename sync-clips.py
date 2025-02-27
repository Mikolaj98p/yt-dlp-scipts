#!/usr/bin/env python3

from yt_dlp import YoutubeDL
from yt_dlp.utils import sanitize_filename, DownloadError
import os
import os.path
import sys
import json
import copy

class StringFormatDict(dict):
  def __getitem__(self, key):
    return sanitize_filename(super().__getitem__(key))

  def __missing__(self, key):
    aliases = {
      "playlist_title": "title"
    }
    if key in aliases:
      return self.get(aliases[key])

    print(f"[DGB] Missing key: {key}") # TODO: tymczasowo

    return "NA"

def get_info(url):
  ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True
  }

  with YoutubeDL(ydl_opts) as ydl: 
    info_dict = ydl.extract_info(url['url'], download=False)
    return info_dict

def download(config, url):
  if 'history_file' in config:
    config['options']['download_archive'] = config.get('history_file') % StringFormatDict(url['extra'])
    print(f"[DBG] Download archive: {config['options']['download_archive']}")
    pass
  
  with YoutubeDL(config['options']) as ydl:
    ydl.download(url['url'])
    pass

  pass

if __name__ == '__main__':
  if not os.path.isfile('configs/sync-clip.json'):
    default_config = {
      "urls": [
        {
          "url": "paste url here",
          "config": "example_cfg",
          "disable": "false",
          "comment-disable": "disable:str optional field allow values: false, afterDownload, skip and true. Default: false"
        }
      ],
      "configs": {
        "example_cfg": {
          "options": {
            "outtmpl": "data/%(playlist_title)s/%(id)s/%(title)s.%(ext)s",
            "format": "bv*[ext=mp4][vcodec^=avc1]+ba*[ext=m4a]",
            "postprocessors": [
              {
                "key": "ExecAfterDownload",
                "exec_cmd": "echo 'data/%(playlist_title)s/%(id)s/'"
              }
            ],
            "writedescription": True,
            "writeinfojson": True,
            "ignoreerrors": "only_download"
          },
          "comment-options": "Object based on yt-dlp module options (ref: https://github.com/yt-dlp/yt-dlp)",
          "history_file": "data/%(playlist_title)s.lst",
          "comment-history_file": "history_file:string optional field allow to format history file path per downloading object from 'playlist' array. Default: do not use history file.",
          "disableAfterDownload": False,
          "comment-disableAfterDownload": "disableAfterDownload:bool optional field, allow to disable all objects from 'playlist' array using config with enabled this field. Default: false",
        }
      }
    }
    if not os.path.exists('configs'):
      os.makedirs('configs')
      pass
    with open('configs/sync-clip.json', 'w') as fo:
      json.dump(default_config, fo, indent=2)
      print("\033[32mSample configuration saved\033[0m")
      pass
    sys.exit(0)
    pass


  with open('configs/sync-clip.json') as f:
    config = json.load(f)

    with open('configs/sync-clip.bck.json', 'w') as fo:
      json.dump(config, fo, indent=2)
      pass
    
    for url in config['urls']:
      try:
        if 'url' not in url or not url['url']:
          continue

        if 'config' not in url or not url['config']:
          continue

        if url.get('disable', 'false') in ['true', 'skip']:
          continue

        url_config_name = url.get('config')

        if url_config_name not in config['configs'] or not config['configs'][url_config_name]:
          continue

        url['extra'] = get_info(url)

        url_config = copy.deepcopy(config['configs'].get(url_config_name))

        if 'retries' in url_config['options'] and url_config['options']['retries'] == 'infinite':
          url_config['options']['retries'] = float('inf')
          pass

        download(url_config, url)

        if url.get('disable', 'false') == 'afterDownload' or url_config.get('disableAfterDownload', False):
          url['disable'] = 'true'
          pass
        
        del url['extra']

        pass
      except DownloadError as e:
        if e.msg.endswith('YouTube said: The playlist does not exist.'):
          pass
        else:
          sys.exit(1)
          pass
        pass
      except Exception as e:
        print(e)
        print({
          "exdended": {
            "url": url,
            "config": config
        }})
        sys.exit(-1)
        pass
      pass
    with open('configs/sync-clip.json', 'w') as fo:
      json.dump(config, fo, indent=2)
    pass
  pass
