package Admin.modules

import geb.Module

/**
 * Contains objects and methods for interacting with the global footer bar.
 */
class FooterModule extends Module {
  static content = {
    // todo update ids/tags
    home { $('#home') }
    copyright { $('#copyright') }
    disclaimer { $('#disclaimer') }
    privacy { $('#privacy') }
    accessibility { $('#privacy') }
    footerBar { $('.app-footer') }
  }

  /**
   * Clicks footer menu anchor tags based on the displayed text.
   * @param [text:'footer link text'] the displayed text of the footer menu anchor tag.
   */
  //  todo either add individual click methods or use gwells unroll method
  void clickMenuItem(Map<String, Object> itemSelector) {
    footerBar.$(itemSelector, 'a').click()
  }
}
