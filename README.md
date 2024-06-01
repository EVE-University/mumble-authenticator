# Alliance Auth - Mumble Authenticator

Requires Alliance Auth to Function. 
<https://gitlab.com/allianceauth/allianceauth/>

## Current Features

- Authenticates Connecting users against the Alliance Auth Database.
- Can provide EVE Avatars to Mumbles Texture feature for use in overlays

## Installation

<https://allianceauth.readthedocs.io/en/latest/features/services/mumble.html>

## Settings

If enabled, textures are automatically set as player's EvE avatar for use on overlay.
`avatar_enable = False`

### Idle Handler
An AFK or Idle handler to move people to a set "AFK" Channel

Enable the Feature
`enabled = False`

Mumble idlesecs Threshold (Seconds) until a user is considered Idle, 
`time = 3600`

Interval(Seconds) to run the Idler Handler at
`interval = 60`

Channel to move Idlers to
`channel = 1`

Idle Handler Ignore or Allowlist, only one of the two can be functional
`denylist = []`
`allowlist = []`

## Docker

Mumble Authenticator can now be used as a Docker container.

This container must share a Docker network with the Auth Database and Mumble, or must otherwise be linked to those containers.

By default when running dockerized the ICE client side port will bind to the 0.0.0.0 interface. This can be controlled with
the MUMBLE_AUTH_ICE_ENDPOINT environment variable or secret file.

### Settings

Both MUMBLE_AUTH_* environment variables and secret files are supported to configure the authenticator process.

Example envfile:
```
MUMBLE_AUTH_DB_NAME="aauth"
MUMBLE_AUTH_DB_USER="aauth"
MUMBLE_AUTH_DB_PASSWORD="securepassword"
MUMBLE_AUTH_DB_HOST="mariadb"

MUMBLE_AUTH_ICE_HOST="mumble"
MUMBLE_AUTH_ICE_SECRET="secret"
```

### Healthcheck
A healthcheck script `healthcheck.py` can be used to monitor the health of your auth process.

The healthcheck script can either load its parameters from the authenticator.ini config or from its command line arguments.

MUMBLE_AUTH_HEALTH_USERNAME, and MUMBLE_AUTH_HEALTH_PASSWORD will set the appropriate configuration with Docker. Otherwise, see
`python healthcheck.py --help` for command line arguments.

This healthcheck requires at a valid username that is listed in Auth MumbleUsers. However, the password is optional unless
you wish to check password verification instead of just user existence.

**NOTE: The user must not exist in the Murmur server database otherwise the healthcheck will give a false positive.**