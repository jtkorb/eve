# OAuth Implementation for EVE Online
#
# Obtain Client ID and Client Secret by registering at https://developers.eveonline.com.  Desired
# scope must also be registered.  The scope entries needed by the application can be determined by
# looking at the API calls requiring authentication at https://esi.tech.ccp.is/latest.
#
CLIENT_ID     = myconf.get('eve.client_id')
CLIENT_SECRET = myconf.get('eve.client_secret')
SCOPE         = myconf.get('eve.scope')

# URLs used by OAuth for EVE Online...
#
VERIFY_URL    = "https://login.eveonline.com/oauth/verify"
AUTH_URL      = "https://login.eveonline.com/oauth/authorize"
TOKEN_URL     = "https://login.eveonline.com/oauth/token"

# Import required modules.
#
from gluon.contrib.login_methods.oauth20_account import OAuthAccount
import requests

# Extend the OAuthAccount class for EVE Online.
#
class EVEAccount(OAuthAccount):
    """OAuth implementation for EVE Online"""

    def __init__(self):
        OAuthAccount.__init__(self, None, CLIENT_ID, CLIENT_SECRET, AUTH_URL, TOKEN_URL, scope=SCOPE)

    def get_user(self):
        '''Returns the user.
        '''
        if not self.accessToken():
            return None

        verify = requests.get(VERIFY_URL, headers={ "Authorization" : "Bearer " + self.accessToken()}).json()

        name = verify['CharacterName'].split()
        id = verify['CharacterID']

        first_name = name[0]
        last_name = " ".join(name[1:]) if len(name) > 1 else None

        return dict(first_name=first_name, last_name=last_name, registration_id=id)

auth.settings.login_form = EVEAccount()
auth.settings.actions_disabled = ['register', 'change_password', 'request_reset_password']
