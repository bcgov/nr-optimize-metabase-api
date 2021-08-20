package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class CommentInstructionsModal extends BaseAppPage {
  static at ={ pageTitle.text() == expectedTitle }
  static content = {
    modalSelector(wait:true) { $('.modal-open .modal-dialog') }
    pageTitle { $('.modal-open .modal-title') }
    closeButton { $('#close') }
    nextButton { $('#next') }
  }
  private final String expectedTitle = 'Submit a Comment'

  void clickNext() {
    nextButton.click()
  }

  void clickClose() {
    closeButton.click()
  }

}
