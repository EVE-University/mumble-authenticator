import logging
import html
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mumble_authenticator import exceptions
from mumble_authenticator.authenticator import ABCAuthenticator
from mumble_authenticator.conf import settings
from hashlib import sha1
from passlib.hash import bcrypt_sha256
from .models import Base, Mumbleuser

logger = logging.getLogger(__name__)


class Authenticator(ABCAuthenticator):
    def __init__(self, server_id):
        super().__init__(server_id)
        db_url = settings.murmur.servers.get(server_id).conf.database_url
        self.engine = create_engine(db_url)
        Base.metadata.bind = self.engine
        self.DBSession = sessionmaker()
        self.DBSession.bind = self.engine

    def authenticate(self, name: str, password: str):
        session = self.DBSession()
        acct = session.query(Mumbleuser).filter_by(username=name).first()
        if acct is None:
            logger.info('Fall through for unknown user {}'.format(name))
            return

        if allianceauth_check_hash(password, acct.pwhash, acct.hashfn):
            logger.info('User authenticated: {}, id: {}'.format(acct.username, acct.user_id))
            # Process groups
            if acct.groups:
                groups = acct.groups.split(',')
            else:
                groups = []

            logger.debug('Groups: {}'.format(groups))
            return acct.user_id, html.unescape(acct.username), groups

        raise exceptions.AuthRefused()

    def get_name(self, id: int):
        session = self.DBSession()
        return session.query(Mumbleuser).filter_by(user_id=id).first()

    def get_id(self, name: str):
        session = self.DBSession()
        return session.query(Mumbleuser).filter_by(username=name).first()

    def shutdown(self):
        self.engine.dispose()


def allianceauth_check_hash(password, hash, hash_type):
    """
    Python implementation of the AllianceAuth MumbleUser hash function
    :param password: Password to be verified
    :param hash: Hash for the password to be checked against
    :param hash_type: Hashing function originally used to generate the hash
    """
    if hash_type == 'sha1':
        return sha1(password).hexdigest() == hash
    elif hash_type == 'bcrypt-sha256':
        return bcrypt_sha256.verify(password, hash)
    else:
        logger.warning("No valid hash function found for {}".format(hash_type))
        return False
