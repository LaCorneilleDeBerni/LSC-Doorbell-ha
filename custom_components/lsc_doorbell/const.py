"""Constants for LSC Smart Connect Video Doorbell integration."""

DOMAIN = "lsc_doorbell"

# Config keys
CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_IP_ADDRESS = "ip_address"
CONF_PROTOCOL_VERSION = "protocol_version"
CONF_RTSP_PORT = "rtsp_port"
CONF_RTSP_PATH = "rtsp_path"

# Defaults
DEFAULT_PORT = 6668
DEFAULT_PROTOCOL_VERSION = "3.3"
DEFAULT_RTSP_PORT = 554
DEFAULT_RTSP_PATH = "/stream0"

# Tuya Datapoints (DPS) pour LSC Doorbell art. 3208999
DP_DOORBELL_BUTTON = 185   # Appui bouton sonnette
DP_MOTION_DETECT  = 115   # Détection de mouvement
DP_PRIVACY_MODE   = 104   # Mode privé (désactive caméra)
DP_RECORDING      = 150   # Enregistrement SD
DP_CHIME          = 136   # Sonnerie intérieure

# Events fired by the integration
EVENT_DOORBELL_PRESSED = "lsc_doorbell_button_pressed"
EVENT_MOTION_DETECTED  = "lsc_doorbell_motion_detected"

# Platforms
PLATFORMS = ["camera", "binary_sensor"]

# Update interval for polling fallback (seconds)
POLLING_INTERVAL = 30
