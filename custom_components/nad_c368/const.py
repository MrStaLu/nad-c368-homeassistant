"""Constants for the NAD C368 integration."""

DOMAIN = "nad_c368"
DEFAULT_NAME = "NAD C368"
DEFAULT_PORT = 8234
DEFAULT_MIN_VOLUME = -80
DEFAULT_MAX_VOLUME = 12
DEFAULT_VOLUME_STEP = 2

CONF_MIN_VOLUME = "min_volume"
CONF_MAX_VOLUME = "max_volume"
CONF_VOLUME_STEP = "volume_step"
CONF_POLL_INTERVAL = "poll_interval"
CONF_SHOW_DB = "show_db"  # dashboard toggle: show volume in dB instead of %

DEFAULT_POLL_INTERVAL = 5  # seconds between state polls

# Source config keys are "source_1" … "source_8"
SOURCE_KEY_PREFIX = "source_"
SOURCE_NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8")

# Enable/disable a source on the amp: SourceN.Enabled=Yes/No
SOURCE_ENABLE_ON = "Yes"
SOURCE_ENABLE_OFF = "No"

DEFAULT_SOURCES: dict[str, str] = {
    "1": "Optical 1",
    "2": "Optical 2",
    "3": "Coaxial 1",
    "4": "Coaxial 2",
    "5": "Phono",
    "6": "Line 1",
    "7": "Line 2",
    "8": "Bluetooth",
}

# NAD RS232 variable names
NAD_POWER = "Main.Power"
NAD_VOLUME = "Main.Volume"
NAD_MUTE = "Main.Mute"
NAD_SOURCE = "Main.Source"
NAD_SPEAKER_A = "Main.SpeakerA"
NAD_SPEAKER_B = "Main.SpeakerB"
NAD_BASS = "Main.Bass"
NAD_TREBLE = "Main.Treble"
NAD_BALANCE = "Main.Balance"
NAD_TONE_DEFEAT = "Main.ToneDefeat"
