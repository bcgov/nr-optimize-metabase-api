package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class CommentSubmitModal extends BaseAppPage {
  static at ={ pageTitle.text() == expectedTitle }
  static content = {
    modalSelector(wait:true) { $('.modal-open .modal-dialog') }
    pageTitle { $('.modal-open .modal-title') }
    closeButton { $('#close') }
    backButton { $('#back') }
    submitButton { $('#submit') }

    nameInput { $('#nameInput') }
    locationInput { $('#locationInput') }
    publishNameCheckbox { $('input[name=anonymous') }
    commentInput { $('#commentInput') }
    // todo file upload

  }
  private final String expectedTitle = 'Submit a Comment'

  void clickBack() {
    backButton.click()
  }

  void clickClose() {
    closeButton.click()
  }

  void clickSubmit() {
    submitButton.click()
  }

  void clickNameVisibility() {
    publishNameCheckbox.click()
  }

  void enterComment(String comment) {
    commentInput.value(comment)
  }

}
