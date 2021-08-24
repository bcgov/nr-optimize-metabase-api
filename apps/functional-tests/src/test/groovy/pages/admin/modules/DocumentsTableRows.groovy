package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException


class DocumentsTableRows extends Module {
  static content = {
      name { $('[data-label=Name]') }
      status { $('[data-label=Status]') }
      date { $('[data-label=Date]') }
      type { $('[data-label=Type]') }
      milestone { $('[data-label=Milestone]') }
  }

  void clickCell() {
      name.click()
  }
}