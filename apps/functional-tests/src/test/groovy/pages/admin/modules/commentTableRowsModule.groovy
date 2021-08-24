package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException


class CommentTableRows extends Module {
  static content = {
      id { $('[data-label=Id]') }
      name { $('[data-label=Author]') }
      date { $('[data-label=Date]') }
      numAttachments { $('[data-label=Attachments]') }
      location { $('[data-label=Location]') }
      status { $('[data-label=Status]') }
  }

  void clickCell() {
      name.click()
  }
}