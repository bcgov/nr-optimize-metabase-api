package Public.modules

import geb.Module

import geb.waiting.WaitTimeoutException

/**
 * Contains objects and methods for interacting with the global header bar.
 */
class HeaderModule extends Module {
  static content = {
    bcLogo { $('.navbar-brand__title') }
    // todo update tags/ids
    findProjects { $('#projectSearch') }
    listProjects { $('#projectList') }
    eaProcess {}
    contactUs { $('#contact') }
    // todo verify this selector is right
    headerNavigationBar { $('#header #mainNav .navbar-nav') }
  }

  /**
   * Clicks header menu anchor tags based on the displayed text.
   *
   * @param [text:'header link text'] the displayed text of the header menu anchor tag.
   */
  void clickMenuItem(Map<String, Object> itemSelector) {
    headerNavigationBar.$(itemSelector, 'a').click()
  }
}
