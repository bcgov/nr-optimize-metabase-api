package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException

//  todo make more generic, this works for projectList in public and admin though
class CPTableRows extends Module {
  static content = {
      stauts { $('[data-label=Status]') }
      startDate { $('[data-label=Start Date') }
      endDate { $('[data-label=End Date') }
      daysRemaining { $('[data-label=Days Remaining') }
      published { $('[data-label=Phase') }
      commentData { $('[data-label=Decision') }
  }

  void clickCell() {
      name.click()
  }
}