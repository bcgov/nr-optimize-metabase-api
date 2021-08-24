package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException

//  todo make more generic, this works for projectList in public and admin though
class TableRows extends Module {
  static content = {
      name { $('[data-label=Name]')}
      proponent ( $('[data-label=Proponent'))
      type ( $('[data-label=Type'))
      region ( $('[data-label=Region'))
      phase ( $('[data-label=Phase'))
      decision ( $('[data-label=Decision'))
  }

  void clickCell() {
      name.click()
  }
}