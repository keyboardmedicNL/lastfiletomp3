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
import config_loader

# vars

current_date = datetime.date.today().strftime("%B %d, %Y")

# functions
def get_twitch_title(token: str) -> tuple[str,dict]:

    response=requests.get(f"https://api.twitch.tv/helix/channels?broadcaster_id={str(loaded_config.twitch_user_id)}",headers={'Authorization':f"Bearer {token}",'Client-Id':loaded_config.twitch_api_id})
    logging.info(f"tried to get twitch title with function get_twitch_title for {str(loaded_config.twitch_user_id)} with response: {response}")
    responsejson = response.json()
    try:
        twitch_title = responsejson["data"][0]["title"]
        logging.info(f"twitch title gotten from twitch api is = {twitch_title}")
    except Exception as e:
        logging.error(f"unable to get title from twitch api")

    return(twitch_title,response)

def get_twitch_api_token() -> str: 
        
        logging.info("Requesting new twitch api auth token from twitch")
        response=requests.post(
                            "https://id.twitch.tv/oauth2/token",
                            json={"client_id" : str(loaded_config.twitch_api_id),
                            "client_secret" : str(loaded_config.twitch_api_secret),
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

    if exists(f"config/token.txt"):
            with open("config/token.txt", 'r') as file2:
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
         f'-ar {str(loaded_config.output_file_samplerate)} '
         f'-ac 2 '
         f'-b:a {str(loaded_config.output_file_bitrate)} '
         f'-metadata artist="{loaded_config.metadata_artist}" '
         f'-metadata title="{file_title} - {current_date}" '
         f'{{}}'
        ).format(video_file_path, audio_file_path)
    subprocess.call(command, shell=True)

def send_message_to_discord():
    logging.info(f"waiting {str(loaded_config.discord_wait_time_minutes)} minutes before posting a notification to discord")

    if loaded_config.discord_wait_time_minutes > 0:
        time.sleep(60*loaded_config.discord_wait_time_minutes)

    data_for_hook = {"content": f"{loaded_config.discord_message}"}
    discord_webhook_response = requests.post(loaded_config.discord_webhook_url, json=data_for_hook, params={'wait': 'true'})

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
    sorted_files = sorted(glob.glob(f"{loaded_config.input_folder_path}*"), key=os.path.getctime, reverse=True)
    video_file = f'"{str(sorted_files[0])}"'
    logging.info(f"latest video file = {video_file}")

    # adds current date to file title (twitch title) and starts conversion
    file_title_stripped_of_invalid_characters = sanitize_filename(file_title)
    audio_file = f'"{loaded_config.output_file_path}{file_title_stripped_of_invalid_characters} - {current_date}.mp3"'
    logging.info(f"getting ready to export to {audio_file}")
    convert_video_to_audio_with_ffmpeg(video_file, audio_file, file_title_stripped_of_invalid_characters)

    #sends notification to discord about your new mix
    if loaded_config.use_discord_notification:
        send_message_to_discord()

    logging.info(f"script finished...")

if __name__ == "__main__":
    loaded_config = config_loader.load_config()
    main()