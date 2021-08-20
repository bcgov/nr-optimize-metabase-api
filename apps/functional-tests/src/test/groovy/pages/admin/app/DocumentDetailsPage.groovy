package Pages.Admin

import geb.waiting.WaitTimeoutException

class DocumentDetailsPage extends BaseAppPage {
  static content = {
    title = { $('h1') }
    actionDropdown { $('#actionDropdown') }
    displayName { $('#displayName') }
    docFileName { $('#documentFileName') }
    description { $('#description') }
    // labels?
    type { $('#type') }
    dateUploaded { $('#dateUploaded') }
    datePosted { $('#datePosted') }
    documentAuthor { $('#documentAuthor') }
    milestone { $('#milestone') }
    projectPhase { $('#projectPhase') }
    internalSize { $('internalSize') }
  }

  void selectAction(String action) {
    actionDropdown.$('.dropdown-item', text:action).click()
  }
}