#!/usr/bin/env bash
set -e

readonly APP_DIR="/app"
readonly BASE_CONFIG_FILE="${APP_DIR}/authenticator.ini.example"
readonly DEFAULT_SECRET_PATHS=(
    "/run/secrets",
    "/etc/secrets",
)

CONFIG_FILE="${APP_DIR}/authenticator.ini"

get_cfg_value() {
    local var="$1"
    local secFile="${MUMBLE_AUTH_SECRET_PATH}/${var}"
    local def="${2:-}"

    local val="$def"
    if [ "${!var:-}" ]; then
        val="${!var}"
    fi

    if [ -r "${secFile}" ]; then
        val="$(< "${!secFile}")"
    fi

    echo -n "$val"
}

# Determine which secret path to use
if [ -z "${MUMBLE_AUTH_SECRET_PATH}"] || [ ! -r "${MUMBLE_SECRET_PATH}" ]; then
    for path in "${DEFAULT_SECRET_PATHS[@]}"; do
        if [ -r "$path" ]; then
            export MUMBLE_AUTH_SECRET_PATH="${path}"
            break
        fi
    done
fi

# Generate config file
cat << EOF > "$CONFIG_FILE"
; Mumble Server Configuration File
;
; This file is autogenerated on container start using MUMBLE_AUTH_* environment variables
; or MUMBLE_AUTH_* files in /run/secrets or /etc/secrets
;
; DO NOT EDIT

[database]
lib = MySQLdb
name = $(get_cfg_value "MUMBLE_AUTH_DB_NAME" "alliance_auth")
user = $(get_cfg_value "MUMBLE_AUTH_DB_USER" "allianceserver")
password = $(get_cfg_value "MUMBLE_AUTH_DB_PASSWORD" "password")
prefix = $(get_cfg_value "MUMBLE_AUTH_DB_PREFIX")
host = $(get_cfg_value "MUMBLE_AUTH_DB_HOST" "127.0.0.1")
port = $(get_cfg_value "MUMBLE_AUTH_DB_PORT" "3306")

[user]
id_offset = $(get_cfg_value "MUMBLE_AUTH_USER_ID_OFFSET" "1000000000")
reject_on_error = $(get_cfg_value "MUMBLE_AUTH_USER_REJCT_ON_ERROR" "True")
avatar_enable = $(get_cfg_value "MUMBLE_AUTH_USER_AVATAR_ENABLE" "False")
ccp_avatar_url = $(get_cfg_value "MUMBLE_AUTH_USER_AVATAR_URL" "https://images.evetech.net/characters/{charid}/portrait?size=32")

[ice]
host = $(get_cfg_value "MUMBLE_AUTH_ICE_HOST" "127.0.0.1")
port = $(get_cfg_value "MUMBLE_AUTH_ICE_PORT" "6502")
slice = $(get_cfg_value "MUMBLE_AUTH_ICE_SLICE" "slices/murmur-1.5.ice")
secret = $(get_cfg_value "MUMBLE_AUTH_ICE_SECRET" "")
watchdog = $(get_cfg_value "MUMBLE_AUTH_ICE_WATCHDOG" "30")
endpoint = $(get_cfg_value "MUMBLE_AUTH_ICE_ENDPOINT" "0.0.0.0")

[murmur]
servers = $(get_cfg_value "MUMBLE_AUTH_MURMUR_SERVERS" "1") 

[log]
level = $(get_cfg_value "MUMBLE_AUTH_LOG_LEVEL" "20") 
file = $(get_cfg_value "MUMBLE_AUTH_LOG_FILE" "")

[iceraw]
Ice.ThreadPool.Server.Size = 5

[idlerhandler]
enabled = $(get_cfg_value "MUMBLE_AUTH_IDLE_ENABLED" "False")
time = $(get_cfg_value "MUMBLE_AUTH_IDLE_TIME" "3600")
interval = $(get_cfg_value "MUMBLE_AUTH_IDLE_INTERVAL" "60")
channel = $(get_cfg_value "MUMBLE_AUTH_IDLE_CHANNEL" "1")
denylist = $(get_cfg_value "MUMBLE_AUTH_IDLE_DENYLIST" "[]")
allowlist = $(get_cfg_value "MUMBLE_AUTH_IDLE_ALLOWLIST" "[]")

[healthcheck]
username = $(get_cfg_value "MUMBLE_AUTH_HEALTH_USERNAME" "healthcheck")
password = $(get_cfg_value "MUMBLE_AUTH_HEALTH_PASSWORD" "")

EOF

if [ "$1" = "bash" ] || [ "$1" = "sh" ]; then
    exec "$@"
fi

exec "python" "authenticator.py" "-a" "$@"