package Public.modules

import geb.Module
import geb.waiting.WaitTimeoutException

/**
 * Contains objects and methods for interacting with the global header bar.
 */
//  todo make more generic, for now this is for projectlist table rows
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