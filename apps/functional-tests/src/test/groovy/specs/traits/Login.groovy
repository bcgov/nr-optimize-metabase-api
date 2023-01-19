package specs.traits

import Pages.Admin.LoginPage
import Pages.Admin.AdminHomePage

/** 
 * Method to login users
 */
trait Login {
  Map env = System.getenv()
  String username = env['LDAP_EMAIL']
  String password = env['LDAP_PASSWORD']

  /**
   * Log in with the test user
   */
  void login() {
    to LoginPage
    usernameField.value(username)
    passwordField.value(password)

    loginButton.click()

    at AdminHomePage
  }
}