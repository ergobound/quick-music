from yt_dlp import YoutubeDL # type: ignore 
# pip install -U yt-dlp
import re
from ytmusicapi import YTMusic

ytmusic = YTMusic()
def get_track_url(song_name):
    search_results = ytmusic.search(song_name, filter="songs")
    print(search_results)
    if search_results:
        track = search_results[0]
        video_id = track['videoId']
        track_url = f"https://music.youtube.com/watch?v={video_id}"
        return track_url
    return None # "Трек не найден"

def my_filter(info_dict):
    # Прямая манипуляция данными перед созданием файла
    delwords = ["band", "topic"]
    for field in ['uploader', 'channel']:
        if info_dict.get(field):
            # Убираем "band" и "topic" (регистронезависимо)
            info_dict[field] = re.sub(
                rf'(?i)\s*[-–—]?\s*({"|".join(delwords)})', '', info_dict[field]
            )
    # Точно так же при желании можно из title удалять к примеру "Official Video"
    return None # Должен возвращать None, чтобы не прерывать загрузку

def download(url: str, audio_only: bool = True,
             playlist_items: str = None, path: str = "music"):
    if audio_only:
        
        output_template = path + "/%(uploader)s-%(title)s.%(ext)s"
        ydl_opts = {
            # 'replace_in_metadata': [{}],
            "format": "bestaudio/best",
            "outtmpl": output_template,
            'match_filter': my_filter, # Вклиниваемся в процесс
            # "sponsorblock_mark": "music_offtopic",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        
    else:
        output_template = path + "/%(title)s.%(ext)s"
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template  
        }

    if playlist_items: ydl_opts["playlist_items"] = playlist_items
    
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# if __name__ == "__main__":
#     link = "https://music.youtube.com/watch?v=c14_LE3Hh5M"
#     download(link, audio_only=True, playlist_items="1,2,3")