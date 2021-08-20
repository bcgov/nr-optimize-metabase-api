package Pages.Public

import geb.waiting.WaitTimeoutException

/**
 * The initial landing page the user is redirected to after logging in.
 */
class MapPage extends BaseAppPage {
  static at = { pageTitle.text() == 'Search Environmental Assessment Projects' }
  static url = '/projects'
  static content = {
    // todo add more selectors
    pageTitle { $('.search-container .additional-filters label') }
    
    baseMapToggle { $('.leaflet-control-layers-toggle') }
    searchInput { $('#applicantInput') }
    searchButton { $('#applyButton') }
    // searchSuggestion { $('')} implement module like tablerows to help select suggested project
  }

  void setSearchTerms(String searchTerms) {
      searchInput.value(searchTerms)
  }

  void clickSearchButton() {
      searchButton.click()
  }


}