package Pages.Public

class ContactUsPage extends BaseAppPage {
  static at = { pageTitle.text() == 'Connect with us...' }
  static url = '/contact'
  static content = {
    pageTitle { $('.hero-banner h1')}
    // external links
      // submit feedback (email)
      // gov directory (site)
      // compliance (email)
      // violations (site)
  }
}
