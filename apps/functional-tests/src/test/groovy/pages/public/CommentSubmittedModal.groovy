package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class CommentSubmittedModal extends BaseAppPage {
  static at ={ pageTitle.text() == expectedTitle }
  static content = {
    modalSelector(wait:true) { $('.modal-open .modal-dialog') }
    pageTitle { $('h4') }
    closeButton { $('#close') }
    backButton { $('#back') }

  }
  private final String expectedTitle = 'Thank you for your comment!'

  void clickBack() {
    backButton.click()
  }

  void clickClose() {
    closeButton.click()
  }
}
