import requests
from os.path import exists
import os
import glob
import subprocess
import datetime

#vars
twitch_api_username = ""
twitch_api_key = ""
twitch_user_id = "115061151"
input_folder_path = "recordings/"
output_file_bitrate = "192k"
output_file_samplerate = "44100"
metadata_artist = "KeyboardMedic"



def get_twitch_title():
    response=requests.get(f"https://api.twitch.tv/helix/channels?broadcaster_id={twitch_user_id}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitch_api_username})
    print(f"tried to get twitch title with function get_twitch_title for {twitch_user_id} with response: {response}")
    responsejson = response.json()
    try:
        twitch_title = responsejson["data"][0]["title"]
    except:
        twitch_title = "unknown title"
    print(f"twitch title gotten from twitch api is = {twitch_title}")
    return(twitch_title,response)

def get_twitch_api_token(): 
        print("Requesting new twitch api auth token from twitch")
        response=requests.post("https://id.twitch.tv/oauth2/token", json={"client_id" : str(twitch_api_username), "client_secret" : str(twitch_api_key), "grant_type":"client_credentials"})
        if "200" in str(response):
            token_json = response.json()
            token = token_json["access_token"]
            print(f"new twitch api auth token is: {token}")
            with open(r'token.txt', 'w') as tokenFile:
                tokenFile.write("%s\n" % token)
        else:
            print(f"unable to request new twitch api auth token with response: {response}")
            token = "empty"
        return(token)

def get_twitch_api_token_from_file():
    if exists(f"token.txt"):
            with open("token.txt", 'r') as file2:
                tokenRaw = str(file2.readline())
                token = tokenRaw.strip()
            print ("twitch api auth token to use for auth: " + token)
    else:
        token = get_twitch_api_token()
    return(token)

def convert_video_to_audio_with_ffmpeg(video_file_path, audio_file_path):
    command = f'ffmpeg -i {{}} -vn -ar {output_file_samplerate} -ac 2 -b:a {output_file_bitrate} -metadata artist="{metadata_artist}" -metadata title="{file_title} - {current_datey}" {{}}'.format(video_file_path, audio_file_path)
    subprocess.call(command, shell=True)

#main
current_date = datetime.date.today().strftime("%B %d, %Y")
#gets token from file or api and loads it to token var
token = get_twitch_api_token_from_file()
#attempts to get twitch title from twitch api with if statement incase twitch api token is invalid
file_title, get_twitch_title_response = get_twitch_title()
if not "200" in str(get_twitch_title_response):
    token = get_twitch_api_token()
    file_title, get_twitch_title_response = get_twitch_title()
# sorts files in input folder by date (last one first) and gets last file
sorted_files = sorted(glob.glob(f"{input_folder_path}*"), key=os.path.getctime, reverse=True)
video_file = f'"{str(sorted_files[0])}"'
print(f"latest video file = {video_file}")
# adds current date to file title (twitch title) and starts conversion
audio_file = f'"{file_title} - {current_date}.mp3"'
print(f"getting ready to export to {audio_file}")
convert_video_to_audio_with_ffmpeg(video_file, audio_file)
print(f"script finished...")



