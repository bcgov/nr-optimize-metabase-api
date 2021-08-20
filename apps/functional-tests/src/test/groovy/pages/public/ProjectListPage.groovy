package Pages.Public

import Public.modules.TableRows
import geb.waiting.WaitTimeoutException

class ProjectListPage extends BaseAppPage {
  static at ={ pageTitle.text() == expectedTitle }
  static url = '/projects-list'
  static content = {
    pageTitle { $('#top .hero-banner h1') }
    closeButton { $('.input-group-append button.btn.btn-primary') }
    advancedSearchButton { $('show-advanced-search-button')}
    searchField { $('#keywordInput') }
    // todo get a count of projects?
    projectList {
        $('table tr').tail().moduleList(TableRows) // tailing to skip header row 
    }
  }
  private final String expectedTitle = 'Environmental Assessments in British Columbia'

  Boolean verifyTitle() {
    pageTitle.text() == expectedTitle
  }

  void clickSearchButton() {
    closeButton.click()
  }

  void clickAdvancedSearchButton() {
    advancedSearchButton.click()
  }

  void setSearchTerms(String searchTerms) {
    searchField.value(searchTerms)
  }

// todo verify what we click is the same each time
  void clickProjectLink() {
      projectList[0].clickCell()
  }
}