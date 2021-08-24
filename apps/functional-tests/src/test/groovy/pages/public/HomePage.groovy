package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class HomePage extends BaseAppPage {
  static at = { pageTitle.text() == 'Environmental Assessments' }
  static url = '/'
  static content = {
    // todo add more selectors
    pageTitle { $('#top .hero-banner h1') }
  }
}
