import logging
import functools
import Ice
from .conf import settings
from . import Murmur


logger = logging.getLogger(__name__)


def ice_protect(return_value=None, exclude: set = (Ice.Exception,), catch_none=True):
    """
    Decorator that protects Ice functions from critical exceptions
    that would cause the authenticator to stop working.
    :param return_value: value to return on caught exception
    :param exclude: Exception classes to exclude and reraise
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if catch_none and result is None:
                    return return_value
                return result
            except Exception as e:
                for x in exclude:
                    if isinstance(e, x):
                        # Excluded exception, reraise
                        raise
                # Not excluded, log and return default value
                logger.exception("Exception in Ice protected function")
                return return_value
        return wrapper
    return decorator


def check_secret(func):
    @functools.wraps(func)
    def wrapper(*args, current=None, **kwargs):
        if not settings.ice.secret:
            return func(*args, **kwargs)
        if not current or 'secret' not in current.ctx or current.ctx['secret'] != settings.ice.secret:
            logger.error('Invalid secret received from server.')
            raise Murmur.InvalidSecretException()
        return func(*args, **kwargs)
    return wrapper
