package Pages.Admin

import geb.Page

class LoginPage extends Page {
    // todo update/sanitize if possible

    static url = "https://sso.pathfinder.gov.bc.ca/auth/realms/eagle/protocol/openid-connect/auth?client_id=eagle-admin-console&response_mode=fragment&response_type=code&scope=openid&redirect_uri=http%3A%2F%2Flocalhost%3A4200%2Fadmin"
    static at = {
        pageTitle.text() == 'EAGLE'
    }
    static content = {
        pageTitle { $('#kc-header-wrapper') }
        usernameField { $('#username') }
        passwordField { $('#password') }
        loginButton { $('#kc-login') }
    }
}