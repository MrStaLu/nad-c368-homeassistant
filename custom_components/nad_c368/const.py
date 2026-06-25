"""Constants for the NAD C368 integration."""

DOMAIN = "nad_c368"
DEFAULT_NAME = "NAD C368"
DEFAULT_PORT = 8234
DEFAULT_MIN_VOLUME = -70
DEFAULT_MAX_VOLUME = -10
DEFAULT_VOLUME_STEP = 2

CONF_MIN_VOLUME = "min_volume"
CONF_MAX_VOLUME = "max_volume"
CONF_VOLUME_STEP = "volume_step"

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

POLL_INTERVAL = 15  # seconds between state polls

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
