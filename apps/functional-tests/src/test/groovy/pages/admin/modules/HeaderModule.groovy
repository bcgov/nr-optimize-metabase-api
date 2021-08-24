package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException

/**
 * Contains objects and methods for interacting with the global header bar.
 */
class HeaderModule extends Module {
  static content = {
    bcLogo { $('.navbar-brand') }
    search { $("a[title|='Search']")}
    calculator { $("a[title|='Open Calculator']") }
    user { $('#welcome') }
    headerNavigationBar { $('#header .navbar') }
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
