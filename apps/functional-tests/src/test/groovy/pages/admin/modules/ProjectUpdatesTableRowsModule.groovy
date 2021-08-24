packages Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException


class ProjectUpdatesTableRows extends Module {
  static content = {
      headline { $('[data-label=Headline]') }
      date { $('[data-label=Date Added]') }
  }

  void clickCell() {
      headline.click()
  }
}