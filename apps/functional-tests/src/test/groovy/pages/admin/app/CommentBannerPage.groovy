package Pages.Admin

import geb.waiting.WaitTimeoutException

class CommentBannerPage extends BaseAppPage {
  static content = {
    viewButton { $('#viewComment') }
    submitButton { $('#submitComment') }
    dateRange { $('.banner h5') }
    description { $('.banner p') }
  }

  void clickSubmitButton() {
    submitButton.click()
  }

  void clickViewButton() {
    viewButton.click()
  }
}