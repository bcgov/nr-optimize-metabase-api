package specs.traits

import Pages.Admin.LoginPage
import Pages.Admin.AdminHomePage

/** 
 * Method to login users
 */
trait Login {
  Map env = System.getenv()
  String username = env['USER_NAME']
  String password = env['USER_PASS']

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