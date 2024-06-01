#!/usr/bin/env python3

import argparse
import logging
import sys

# Defaults
config_file = "authenticator.ini"
default_config = {
    "ice": (
        ("host", str, "127.0.0.1"),
        ("port", int, 6502),
        ("slice", str, "slices/murmur-1.5.ice"),
        ("secret", str, ""),
    ),
    "murmur": (("servers", lambda x: list(map(int, x.split(","))), []),),
    "healthcheck": (
        ("username", str, "healthcheck_user"),
        ("password", str, ""),
    ),
}

# Logger setup
logger = logging.getLogger("healthcheck")

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

# Parse command line arguments
parser = argparse.ArgumentParser(
    prog="Healthcheck",
    description="Mumble auth healthcheck script",
    add_help=False,
)

parser.add_argument(
    "-H",
    "--help",
    action="help",
    help="Show help message and exit",
)
parser.add_argument(
    "-c",
    "--config",
    type=str,
    help="Config file to use",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Verbose logging equivalent to -l DEBUG",
)
parser.add_argument(
    "-l",
    "--level",
    type=str,
    help="Set log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
)

parser.add_argument(
    "-u",
    "--user",
    type=str,
    help="Mumble username",
)

parser.add_argument(
    "-p",
    "--password",
    type=str,
    help="Mumble password",
)

parser.add_argument(
    "-h",
    "--host",
    type=str,
    help="ICE host",
)

parser.add_argument(
    "-P",
    "--port",
    type=int,
    help="ICE port",
)

parser.add_argument(
    "-s",
    "--secret",
    type=str,
    help="ICE secret",
)

parser.add_argument(
    "-S",
    "--slice",
    type=str,
    help="ICE slice path",
)

args = parser.parse_args()

# Import deps that require ICE after argument parsing so --help can be used without installing zeroc-ice.
import Ice
from authenticator import config as AuthConfig

if args.config is not None:
    logger.debug(f"Using custom config file {args.config}")
    config_file = args.config

if args.verbose:
    logger.setLevel(logging.DEBUG)
    logger.debug(f"Using verbose mode")

if args.level is not None and not args.verbose:
    label = args.level.upper()
    level = logging.WARNING
    if label == "DEBUG":
        level = logging.DEBUG
    elif label == "INFO":
        level = logging.INFO
    elif label == "WARNING" or label == "WARN":
        level = logging.WARNING
    elif label == "ERROR":
        level = logging.ERROR
    elif level == "CRITICAL":
        level = logging.CRITICAL
    else:
        logger.warning(f'Unknown log level "{label}"')
        label = "WARNING"

    logger.setLevel(level)
    logger.debug(f"Using log level {label}")

config = AuthConfig(config_file, default_config)

if args.user is not None:
    config.healthcheck.username = args.user

if args.password is not None:
    config.healthcheck.password = args.password

if args.host is not None:
    config.ice.host = args.host

if args.port is not None:
    config.ice.port = args.port

if args.secret is not None:
    config.ice.secret = args.secret

if args.slice is not None:
    config.ice.slice = args.slice


logger.debug(
    f"Healthcheck Mumble credentials User: {config.healthcheck.username}, Pass: {config.healthcheck.password}"
)

# ICE Initialization
slicedir = Ice.getSliceDir()

logger.debug(f"Loading slice: {config.ice.slice}")
Ice.loadSlice(config.ice.slice, ["-I" + slicedir])

# ICE Slice module was changed from Murmur to MumbleServer in 1.5
try:
    import Murmur

    logger.debug("Using pre-1.5 slice.")
except ImportError:
    import MumbleServer as Murmur

    logger.debug("Using post-1.5 slice.")

ice_init_data = Ice.InitializationData()
ice_init_data.properties = Ice.createProperties(sys.argv)
# Default is 60 seconds which is a bit too long
ice_init_data.properties.setProperty("Ice.Default.Timeout", "10000")
# Default is unlimited since ICE 3.6 which will cause the app to hang if the endpoint filters instead of rejecting the connection.
ice_init_data.properties.setProperty("Ice.Default.InvocationTimeout", "5000")
ice_init_data.properties.setProperty("Ice.ImplicitContext", "Shared")

with Ice.initialize(ice_init_data) as ice:
    logger.info(f"Setting up ICE connection to {config.ice.host}:{config.ice.port}.")
    if config.ice.secret:
        logger.debug("Using ICE secret")
        ice.getImplicitContext().put("secret", config.ice.secret)

    base = ice.stringToProxy(f"Meta:tcp -h {config.ice.host} -p {config.ice.port}")
    meta = Murmur.MetaPrx.uncheckedCast(base)

    failure = False

    try:
        servers = meta.getBootedServers()
        logger.info("ICE Connection successful.")
    except Murmur.InvalidSecretException:
        logger.fatal(
            f"{config.ice.host}:{config.ice.port} - ICE returned Invalid ICE Secret error"
        )
        exit(1)
    except Ice.TimeoutException:
        logger.fatal(
            f"{config.ice.host}:{config.ice.port} - ICE connection or operation timed out"
        )
        exit(1)
    except Ice.ConnectionRefusedException:
        logger.fatal(f"{config.ice.host}:{config.ice.port} - ICE connection refused")
        exit(1)
    except Ice.DNSException as e:
        logger.fatal(f"{config.ice.host}:{config.ice.port} - Invalid ICE hostname")
        exit(1)

    logger.info(f"Checking health on {len(servers)} virtual servers.")
    logger.debug(f"Virtual Server ID(s): {', '.join([str(s.id()) for s in servers])}")

    for server in servers:
        if not config.murmur.servers or server.id() in config.murmur.servers:
            try:
                ret = server.verifyPassword(
                    config.healthcheck.username, config.healthcheck.password
                )
            except Ice.TimeoutException:
                logger.error(
                    f"Verify Password call to virtual server {server.id()} timed out"
                )
                ret = -2

            logger.debug(f"Server: {server.id()} Ret: {ret}")
            if config.healthcheck.password:
                if ret == -1:
                    logger.debug(f"Virtual server {server.id()}: Password failure")
                    failure = True
            if ret == -2:
                logger.debug(f"Virtual server {server.id()}: Username failure")
                failure = True

    if failure:
        logger.info("Healthcheck failure.")
    else:
        logger.info("Healthcheck success.")

    exit(failure)
