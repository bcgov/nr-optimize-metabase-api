package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException

/**
 * Contains objects and methods for interacting with the global header bar.
 */
class NavBarModule extends Module {
  static content = {
    breadcrumb { $('.breadcrumb') }
    activeBreadcrumb { $('.breadcrumb active') }
    navBar { $('.action-container') }
    // todo determine best way to handle the changing button in the navbar,based on what's selected in project details menu
    actionsDropdown { $('#actionDropdown') }
    newCPButton { $('#add') }
  }

  void clickNewCP() {
    newCPButton.click()
  }
}