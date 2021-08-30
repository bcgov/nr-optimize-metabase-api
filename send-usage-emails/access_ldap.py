
import argparse
import constants
import ldap3
import logging
import nslookup
from getpass import getpass

LOGGER = logging.getLogger("DEBUG")


class LDAPUtil():
    def __init__(self, user, passwd):
        self.user = user
        self.passwd = passwd
        self.server = None
        self.serverSrc = LDAPServer()

    def getLdapConnection(self):
        for server_ip in self.serverSrc:
            LOGGER.debug(f"trying the ip: {server_ip}")
            server = ldap3.Server(server_ip)
            try:
                # Note: {self.serverSrc.defaultDomain} only works as "idir" on dev pc
                print(f"Trying: idir\\{self.user} with {self.passwd}")
                conn = ldap3.Connection(server, user=f"idir\\{self.user}", password=f"{self.passwd}", auto_bind=True, authentication=ldap3.NTLM)
                break
            except ldap3.core.exceptions.LDAPSocketOpenError:
                msg = 'problem connecting to ldap server {server_ip}... trying a different server'
                LOGGER.WARNING(msg)
            except ldap3.core.exceptions.LDAPBindError:
                msg = f'Credentials are likely incorrect for idir\\{self.user}, password={self.passwd}'
                LOGGER.WARNING(msg)
        return conn

    def getUserEmail(self, inputUserName):
        conn = self.getLdapConnection()
        if conn is None:
            return None
        # todo: calc this from default domain
        hoststring = 'OU=BCGOV,DC=idir,DC=BCGOV'
        queryString = f'(&(objectClass=person)(mailNickname={inputUserName.upper()}))'
        conn.search(hoststring, search_filter=queryString, search_scope='SUBTREE', attributes='*')
        if len(conn.response) > 0:
            LOGGER.debug(conn.response)
            email = conn.response[0]['attributes']['mail']
        else:
            msg = 'user: {inputUserName} not found in ldap'
            LOGGER.WARNING(msg)
        return email


class LDAPServer():

    def __init__(self):
        self.defaultDomain = "idir.bcgov"
        self.serverIPList = []
        self.curServ = 0
        self.getServerList()

    def __iter__(self):
        return self

    def __next__(self):
        if self.curServ >= len(self.serverIPList):
            raise StopIteration
        retVal = self.serverIPList[self.curServ]
        self.curServ += 1
        return retVal

    def getServerList(self):
        self.serverIPList = []
        dns_query = nslookup.Nslookup()
        ips_record = dns_query.dns_lookup(self.defaultDomain)
        for server_ip in ips_record.answer:
            self.serverIPList.append(server_ip)


# if command line arguments were provided, override constants.py provided environment variables
def handle_input_arguments():
    parser = argparse.ArgumentParser()
    # access_ldap.py -objstor_admin <objstor_admin> -objstor_pass <objstor_pass> -postgres_user <postgres_user> -postgres_pass <postgres_pass>"

    parser.add_argument(
        "-ldap_user",
        "--ldap_user",
        dest="ldap_user",
        required=False,
        help="ldap account for accessing active directory",
        metavar="string",
        type=str
    )
    parser.add_argument(
        "-ldap_pass",
        "--ldap_pass",
        dest="ldap_pass",
        required=False,
        help="ldap password for accessing active directory",
        metavar="string",
        type=str
    )

    args = parser.parse_args()

    # Override constants
    if args.ldap_user is not None:
        constants.LDAP_USER = args.ldap_user
    if args.ldap_pass is not None:
        constants.LDAP_PASSWORD = args.ldap_pass
    if constants.LDAP_PASSWORD == "":
        constants.LDAP_PASSWORD = getpass()


if __name__ == '__main__':
    handle_input_arguments()
    LOGGER = logging.getLogger()
    LOGGER.setLevel(logging.INFO)
    hndlr = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
    hndlr.setFormatter(formatter)
    LOGGER.addHandler(hndlr)
    LOGGER.debug("test")

    srvr = LDAPServer()
    for ip in srvr:
        print(f'ldap srvr ip: {ip}')

    util = LDAPUtil(constants.LDAP_USER, constants.LDAP_PASSWORD)
    inputUser = 'ssharp'
    email = util.getUserEmail(inputUser)
    LOGGER.info(f"email for {inputUser} is: {email}")
