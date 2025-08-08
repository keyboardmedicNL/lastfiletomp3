import housey_logging
housey_logging.configure()

import requests
from os.path import exists
import os
import glob
import subprocess
import datetime
import time
import re
import logging

# vars
# do not touch anything above this!!!
twitch_api_username = "YOUR_TWITCH_API_ID"
twitch_api_key = "YOUR_TWITCH_API_SECRET"
twitch_user_id = "YOUR_TWITCH_UUID"

input_folder_path = "PATH/TO/INPUT/FILES"
output_file_path = 'PATH/TO/OUTPUT/FOLDER'
output_file_bitrate = "192k"
output_file_samplerate = "44100"
metadata_artist = "YOUR_ARTIST_NAME"

discord_webhook = "YOUR_DISCORD_WEBHOOK_URL"
discord_message = "YOUR_DISCORD_NOTIFICATION_MESSAGE"
discord_message_wait_time_minutes = 1
use_discord_notification = True

# do not touch anything below here!!!

current_date = datetime.date.today().strftime("%B %d, %Y")

# functions
def get_twitch_title(token: str) -> tuple[str,dict]:

    response=requests.get(f"https://api.twitch.tv/helix/channels?broadcaster_id={twitch_user_id}",headers={'Authorization':f"Bearer {token}",'Client-Id':twitch_api_username})
    logging.info(f"tried to get twitch title with function get_twitch_title for {twitch_user_id} with response: {response}")
    responsejson = response.json()
    twitch_title = responsejson["data"][0]["title"]
    logging.info(f"twitch title gotten from twitch api is = {twitch_title}")

    return(twitch_title,response)

def get_twitch_api_token() -> str: 
        
        logging.info("Requesting new twitch api auth token from twitch")
        response=requests.post(
                            "https://id.twitch.tv/oauth2/token",
                            json={"client_id" : str(twitch_api_username),
                            "client_secret" : str(twitch_api_key),
                            "grant_type":"client_credentials"}
                            )
        
        if response.ok:
            token_json = response.json()
            token = token_json["access_token"]
            logging.info(f"new twitch api auth token recieved from twitch")

            with open(r'token.txt', 'w') as tokenFile:
                tokenFile.write("%s\n" % token)

        else:
            logging.error(f"unable to request new twitch api auth token with response: {response}")
            token = "empty"

        return(token)

def get_twitch_api_token_from_file() -> str:

    if exists(f"token.txt"):
            with open("token.txt", 'r') as file2:
                tokenRaw = str(file2.readline())
                token = tokenRaw.strip()
            logging.info ("twitch api auth token to use loaded from file")

    else:
        token = get_twitch_api_token()
    return(token)


def convert_video_to_audio_with_ffmpeg(video_file_path: str, audio_file_path: str, file_title: str):
    command = (
         f'ffmpeg -i {{}} '
         f'-vn '
         f'-ar {output_file_samplerate} '
         f'-ac 2 '
         f'-b:a {output_file_bitrate} '
         f'-metadata artist="{metadata_artist}" '
         f'-metadata title="{file_title} - {current_date}" '
         f'{{}}'
        ).format(video_file_path, audio_file_path)
    subprocess.call(command, shell=True)

def send_message_to_discord():
    logging.info(f"waiting {str(discord_message_wait_time_minutes)} minutes before posting a notification to discord")

    if discord_message_wait_time_minutes > 0:
        time.sleep(60*discord_message_wait_time_minutes)

    data_for_hook = {"content": f"{discord_message}"}
    discord_webhook_response = requests.post(discord_webhook, json=data_for_hook, params={'wait': 'true'})

    logging.info(f"posting message to discord, response is {discord_webhook_response}")

def sanitize_filename(name: str, replacement: str="_") -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)
    sanitized = sanitized.strip(" .")

    return sanitized if sanitized else "unnamed"

#main
def main():
    #gets token from file or api and loads it to token var
    token = get_twitch_api_token_from_file()

    #attempts to get twitch title from twitch api with if statement incase twitch api token is invalid
    file_title, get_twitch_title_response = get_twitch_title(token)
    if not get_twitch_title_response.ok:
        token = get_twitch_api_token()
        file_title, get_twitch_title_response = get_twitch_title(token)

    # sorts files in input folder by date (last one first) and gets last file
    sorted_files = sorted(glob.glob(f"{input_folder_path}*"), key=os.path.getctime, reverse=True)
    video_file = f'"{str(sorted_files[0])}"'
    logging.info(f"latest video file = {video_file}")

    # adds current date to file title (twitch title) and starts conversion
    file_title_stripped_of_invalid_characters = sanitize_filename(file_title)
    audio_file = f'"{output_file_path}{file_title_stripped_of_invalid_characters} - {current_date}.mp3"'
    logging.info(f"getting ready to export to {audio_file}")
    convert_video_to_audio_with_ffmpeg(video_file, audio_file, file_title_stripped_of_invalid_characters)

    #sends notification to discord about your new mix
    if use_discord_notification:
        send_message_to_discord()

    logging.info(f"script finished...")

if __name__ == "__main__":
    main()