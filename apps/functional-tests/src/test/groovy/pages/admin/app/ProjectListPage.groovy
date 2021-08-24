package Pages.Admin

import Admin.modules.TableRows
import geb.waiting.WaitTimeoutException

class ProjectListPage extends BaseAppPage {
  static at = { }
  static url = '/projects'
  static content = {
    // todo get a count of projects?
    projectList {
        $('table tr').tail().moduleList(TableRows) // tailing to skip header row 
    }
  }
 

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
  String clickProjectLink() {
      projectList[0].clickCell()
      return projectList[0].name
  }
}