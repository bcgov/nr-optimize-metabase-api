package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException


class WorkingGroupTableRows extends Module {
  static content = {
      select { $('[data-label=Select]') }
      name { $('[data-label=Name]') }
  }

  void clickCell() {
      name.click()
  }
}