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
DEFAULT_PROTOCOL_VERSION = "3.5"
DEFAULT_RTSP_PORT = 554
DEFAULT_RTSP_PATH = "/stream0"

# Tuya Datapoints (DPS) pour LSC Doorbell art. 3208999
# Découverts expérimentalement avec discover_dps.py
DP_DOORBELL_BUTTON  = 212   # Appui bouton sonnette + photo (JSON base64)
DP_MOTION_DETECT    = 149   # Détection de mouvement (True/False)
DP_BATTERY          = 145   # Niveau de batterie (%)
DP_STATUS           = 146   # Statut général
DP_MOTION_SENSITIVE = 108   # Sensibilité détection mouvement (low/medium/high)

# Events fired by the integration
EVENT_DOORBELL_PRESSED = "lsc_doorbell_button_pressed"
EVENT_MOTION_DETECTED  = "lsc_doorbell_motion_detected"

# Platforms
PLATFORMS = ["binary_sensor", "sensor", "select"]

# Update interval for polling fallback (seconds)
POLLING_INTERVAL = 30

# Motion sensitivity levels
MOTION_SENSITIVITY_OPTIONS = ["low", "medium", "high"]
