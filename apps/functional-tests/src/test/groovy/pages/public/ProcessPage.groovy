package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class ProcessPage extends BaseAppPage {
  static at = { pageTitle.text() == 'Process & Procedures' }
  static url = '/process'
  static content = {
    // todo add more selectors
    pageTitle { $('#top .hero-banner h1') }
  }
}