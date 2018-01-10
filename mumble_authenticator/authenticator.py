# -*- coding: utf-8 -*-
from abc import ABCMeta
from typing import TypeVar, Iterable, Tuple, Union
from .decorators import ice_protect, check_secret
from .conf import settings
from . import Murmur, exceptions


class ABCAuthenticator(metaclass=ABCMeta):
    def __init__(self, server_id):
        self.server_id = server_id

    def authenticate(self, name: str, password: str) -> Union[None, (int, str, list)]:
        """
        Authenticate an incoming connection attempt.
        Raise exception AuthRefused on an authentication failure.
        Return None to pass through to other authentication methods.
        :param name: Username to authenticate
        :param password: Password to authenticate with
        :return: Tuple (user_id, username, groups) or None to pass through
        """
        raise NotImplemented

    def get_info(self, id: int):
        """
        TODO: Im not sure what this is supposed to return
        :param id:
        :return:
        """
        pass

    def get_id(self, name: str) -> Union[int, None]:
        """
        Get a users ID by their name
        :param name: username to get ID for
        :return: users ID or None to fall through (e.g. not found)
        """
        raise NotImplemented

    def get_name(self, id: int) -> Union[str, None]:
        """
        Get a users username by their ID
        :param id: users ID to get username for
        :return: users username or None to fall through (e.g. not found)
        """
        raise NotImplemented

    def get_texture(self, id: int):
        """
        TODO: Im not sure what this is supposed to return
        :param id:
        :return:
        """
        pass

    def shutdown(self):
        """
        Called when the authenticator is shutting down
        """
        pass


authenticate_default = (-1, None, None)

try:
    if settings.user.reject_on_error:
        authenticate_default = (-2, None, None)
except AttributeError:
    pass


class MurmurAdapter(Murmur.ServerAuthenticator):
    """
    Adapts the generated class from Murmur.ice to our internal pretty class (◕ᴗ◕✿)
    :param authenticator: Authenticator instance to use with this adapter
    """
    def __init__(self, authenticator: ABCAuthenticator):
        self.auth = authenticator
        self.id_offset = settings.murmur.servers.get(self.auth.server_id).id_offset
        super().__init__()

    @ice_protect(authenticate_default)
    @check_secret
    def authenticate(self, name: str, pw: str, certificates, certhash, certstrong: bool) -> (int, str, list):
        """
        Called to authenticate a user. If you do not know the username in question, always return -2 from this
        method to fall through to normal database authentication.
        Note that if authentication succeeds, murmur will create a record of the user in it's database, reserving
        the username and id so it cannot be used for normal database authentication.
        The data in the certificate (name, email addresses etc), as well as the list of signing certificates,
        should only be trusted if certstrong is true.

        Internally, Murmur treats usernames as case-insensitive. It is recommended
        that authenticators do the same. Murmur checks if a username is in use when
        a user connects. If the connecting user is registered, the other username is
        kicked. If the connecting user is not registered, the connecting user is not
        allowed to join the server.
        :param name Username to authenticate.
        :param pw Password to authenticate with.
        :param certificates List of der encoded certificates the user connected with.
        :param certhash Hash of user certificate, as used by murmur internally when matching.
        :param certstrong True if certificate was valid and signed by a trusted CA.
        :param newname Set this to change the username from the supplied one.
        :param groups List of groups on the root channel that the user will be added to for the duration of the connection.
        :return UserID of authenticated user, -1 for authentication failures, -2 for unknown user (fallthrough),
                -3 for authentication failures where the data could (temporarily) not be verified.
        """
        try:
            result = self.auth.authenticate(name, pw)
            if result[0] >= 0:
                # Add ID offset
                result = (result[0] + self.id_offset, result[1], result[2])
            return result
        except exceptions.AuthRefused:
            return -1, None, None

    @ice_protect((False, None))
    @check_secret
    def getInfo(self, id: int):
        """
        Fetch information about a user. This is used to retrieve information like email address, keyhash etc. If you
        want murmur to take care of this information itself, simply return false to fall through.
        :param id User id.
        :param info Information about user. This needs to include at least "name".
        :return true if information is present, false to fall through.
        """
        return self.auth.get_info(id - self.id_offset)

    @ice_protect(-2)
    @check_secret
    def nameToId(self, name: str) -> int:
        """
        Map a name to a user id.
        :param name Username to map.
        :return User id or -2 for unknown name.
        """
        result = self.auth.get_id(name)
        return result + self.id_offset if result >= 0 else None

    @ice_protect("")
    @check_secret
    def idToName(self, id: int) -> str:
        """
        Map a user id to a username.
        :param id User id to map.
        :return Name of user or empty string for unknown id.
        """
        return self.auth.get_name(id - self.id_offset)

    @ice_protect("")
    @check_secret
    def idToTexture(self, id: int):
        """
        Map a user to a custom Texture.
        :param id User id to map.
        :return User texture or an empty texture for unknown users or users without textures.
        """
        return self.auth.get_texture(id - self.id_offset)
