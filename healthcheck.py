#!/usr/bin/env python3

import logging
import sys

import Ice

from authenticator import config as AuthConfig

slicedir = Ice.getSliceDir()
Ice.loadSlice("/app/Murmur.ice", ["-I" + slicedir])

import Murmur

# Defaults
config_file = "authenticator.ini"
default_config = {
    "ice": (
        ("host", str, "127.0.0.1"),
        ("port", int, 6502),
        ("slice", str, "Murmur.ice"),
        ("secret", str, ""),
    ),
    "murmur": (("servers", lambda x: list(map(int, x.split(",")), [])),),
    "healthcheck": (
        ("username", str, "healthcheck_user"),
        ("password", str, ""),
    ),
}

config = AuthConfig(config_file, default_config)

logger = logging.getLogger("healthcheck")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

logger.debug(f"User: {config.healthcheck.username}, Pass: {config.healthcheck.password}")

ice_init_data = Ice.InitializationData()
ice_init_data.properties = Ice.createProperties(sys.argv)
ice_init_data.properties.setProperty("Ice.ImplicitContext", "Shared")


with Ice.initialize(ice_init_data) as ice:
    if config.ice.secret:
        logger.debug("Using ICE secret")
        ice.getImplicitContext().put("secret", config.ice.secret)

    base = ice.stringToProxy(f"Meta:tcp -h {config.ice.host} -p {config.ice.port}")
    meta = Murmur.MetaPrx.uncheckedCast(base)

    failure = False

    try:
        servers = meta.getBootedServers()
    except Murmur.InvalidSecretException:
        logger.fatal("Murmur ICE returned Invalid ICE Secret error")
        exit(1)
    except Ice.TimeoutException:
        logger.fatal("Murmur ICE connection or operation timed out")
        exit(1)
    except Ice.DNSException as e:
        logger.fatal(f"Invalid ICE hostname: {e.host}")
        exit(1)

    for server in servers:
        if not config.murmur.servers or server.id() in config.murmur.servers:
            try:
                ret = server.verifyPassword(
                    config.healthcheck.username, config.healthcheck.password
                )
            except Ice.TimeoutException:
                logger.error(f"Verify Password call to virtual server {server.id()} timed out")
                ret = -2

            logger.debug(f"Server: {server.id()} Ret: {ret}")
            if config.healthcheck.password:
                if ret == -1:
                    logger.debug("Password failure")
                    failure = True
            if ret == -2:
                logger.debug("Username failure")
                failure = True

    exit(failure)
