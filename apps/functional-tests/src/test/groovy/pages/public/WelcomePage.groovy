package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class WelcomePage extends BaseAppPage {
  static at ={ pageTitle.text() == 'Welcome to New EPIC!' }
  static content = {
    modalSelector(wait:true) { $('.modal-open .splash-modal') }
    pageTitle { $('.modal-open .splash-modal h2') }
    closeButton { $('.modal-open .splash-modal .close-btn')}
  }
  private final String expectedTitle = 'Welcome to New EPIC!'

  Boolean verifyWelcomeContent() {
    pageTitle.text() == expectedTitle
  }

  void clickCloseButton() {
    closeButton.click()
  }
}
