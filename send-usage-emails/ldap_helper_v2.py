import constants
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPBindError

from log_helper import LOGGER


class LDAPUtil():
    def __init__(self, user=constants.LDAP_USER, passwd=constants.LDAP_PASSWORD):
        self.user = user
        self.passwd = passwd
        self.server = None
        self.serverSrc = LDAPServer()

    def getLdapConnection(self):
        conn = None
        server = Server(constants.LDAP_DOMAIN, get_info=ALL)
        try:
            LOGGER.debug(f"Trying: AUTHTEST\\{self.user} with {self.passwd}")
            conn = Connection(server, user=f"AUTHTEST\\{self.user}", password=f"{self.passwd}", auto_bind=True, authentication=NTLM)
        except LDAPBindError:
            msg = f'Credentials are likely incorrect for idir\\{self.user}, password={self.passwd}'
            LOGGER.warning(msg)
        except (Exception) as error:
            LOGGER.warning(f"Failed to connect to ldap server, error: {error}")
        return conn

    def getADInfo(self, idir, conn=None, out_attributes=["givenName", "mail"]):
        user_info = {
            "givenName": None
        }
        if conn is None:
            conn = self.getLdapConnection()
        if conn is None:
            return None
      
        host_string = 'OU=BCGOV,DC=idir,DC=BCGOV'

        query_String = "(&(objectclass=user)" \
            "(&(SamAccountName={})))" \
            .format(idir.upper())
       
        conn.search(search_base=host_string, search_filter=query_String, search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)

        if len(conn.response) > 0:
            LOGGER.debug(conn.response)
            if out_attributes == '*':
                for attribute in conn.response[0]['attributes']:
                    user_info[attribute] = conn.response[0]['attributes'][attribute]                   
            else:
                for attribute in out_attributes:
                    user_info[attribute] = conn.response[0]['attributes'][attribute]
        else:
            msg = f'user: {idir} not found in ldap'
            LOGGER.warning(msg)
        return user_info


class LDAPServer():

    def __init__(self):
        self.defaultDomain = constants.LDAP_DOMAIN

    def __iter__(self):
        return self


if __name__ == '__main__':

    util = LDAPUtil(constants.LDAP_USER, constants.LDAP_PASSWORD)
    inputUser = 'ssharp'
    email = util.getADInfo(inputUser)
    LOGGER.info(f"email for {inputUser} is: {email}")
    