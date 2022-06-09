import constants
import ldap3
import nslookup

from log_helper import LOGGER


class LDAPUtil():
    def __init__(self, user=constants.LDAP_USER, passwd=constants.LDAP_PASSWORD):
        self.user = user
        self.passwd = passwd
        self.server = None
        self.serverSrc = LDAPServer()

    def getLdapConnection(self):
        conn = None
        self.serverSrc.curServ = 0
        for server_ip in self.serverSrc:
            LOGGER.debug(f"trying the ip: {server_ip}")
            server = ldap3.Server(server_ip)
            try:
                # Note: {self.serverSrc.defaultDomain} only works as "idir" on dev pc
                LOGGER.debug(f"Trying: idir\\{self.user} with {self.passwd}")
                conn = ldap3.Connection(server, user=f"idir\\{self.user}", password=f"{self.passwd}", auto_bind=True, authentication=ldap3.NTLM)
                break
            except ldap3.core.exceptions.LDAPSocketOpenError:
                msg = f'problem connecting to ldap server {server_ip}... trying a different server'
                LOGGER.warning(msg)
            except ldap3.core.exceptions.LDAPBindError:
                msg = f'Credentials are likely incorrect for idir\\{self.user}, password={self.passwd}'
                LOGGER.warning(msg)
            except (Exception) as error:
                LOGGER.warning(f"Failed to connect to ldap server, error: {error}")
        return conn

    def getADInfo(self, idir, conn=None):
        user_info = {
            "givenName": None
        }
        if conn is None:
            conn = self.getLdapConnection()
        if conn is None:
            return None
        # todo: calc this from default domain
        host_string = 'OU=BCGOV,DC=idir,DC=BCGOV'
        # query_String = f'(&(objectClass=person)(mailNickname={idir.upper()}))'
        query_String = f'(samaccountname={idir.upper()})'
        conn.search(host_string, search_filter=query_String, search_scope='SUBTREE', attributes='*')
        if len(conn.response) > 0:
            LOGGER.debug(conn.response)
            user_info["department"] = conn.response[0]['attributes']['department']
            user_info["givenName"] = conn.response[0]['attributes']['givenName']
        else:
            msg = f'user: {idir} not found in ldap'
            LOGGER.warning(msg)
        return user_info


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


if __name__ == '__main__':

    # srvr = LDAPServer()
    # for ip in srvr:
    #    print(f'ldap srvr ip: {ip}')

    util = LDAPUtil(constants.LDAP_USER, constants.LDAP_PASSWORD)
    inputUser = 'ssharp'
    email = util.getADInfo(inputUser)
    LOGGER.info(f"email for {inputUser} is: {email}")
