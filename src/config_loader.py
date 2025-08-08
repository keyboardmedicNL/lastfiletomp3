import yaml
import logging

default_config = {
    "output_file_bitrate": "192k",
    "output_file_samplerate": "44100",
    "discord_message_wait_time_minutes": 1,
    "use_discord_notification": False,
    "metadate_artist": "",
    "discord_webhook_url": "",
    "discord_message": ""
}

# loads config from file
def load_config() -> dict:
    with open("config/config.yaml") as config_file:
        config_yaml = yaml.safe_load(config_file)
        merged_config = config_object({**default_config, **config_yaml})
        logging.debug("succesfully loaded config")        
        return(merged_config)


class config_object:
    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)
