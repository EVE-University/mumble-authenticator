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
