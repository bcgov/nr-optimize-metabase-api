package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class LegislationPage extends BaseAppPage {
  static at = { pageTitle.text() == 'Legislation' }
  static url = '/legislation'
  static content = {
    // todo add more selectors
    pageTitle { $('#top .hero-banner h1') }
  }
}