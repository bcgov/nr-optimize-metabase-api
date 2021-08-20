package Pages.Admin

import Admin.modules.DocumentsTableRows
import geb.waiting.WaitTimeoutException

class ProjectDocumentsPage extends BaseAppPage {
  static at = {}
  static content = {
    searchInput { $('#keywordInput') }
    searchButton { $('[type=submit]') }
    helpButton { $('.btn-search-help') }
    numItemsDropdown { $('#actionDropdown') }

    selectAllButton { $('#button-sa') }
    editButton { $('#button-e') }
    publishButton { $('#button-p') }
    unpublishButton { $('#button-u') }
    linkButton { $('#button-l') }
    donwloadButton { $('#button-dl') }
    deleteButton { $('#button-d') }
    uploadButton { $('.upload-docs #button-d') }

    documentList {
        $('table tr').tail().moduleList(DocumentsTableRows) // tailing to skip header row 
    }
  }

  void setSearchTerms(String searchTerms) {
    searchInput.value(searchTerms)
  }

  void clickSearchButton() {
    searchButton.click()
  }

  void clickHelpButton() {
    helpButton.click()
  }

  void clickSelectAll() {
    selectAllButton.click()
  }

  void clickEditButton() {
    editButton.click()
  }

  void clickPublishButton() {
    publishButton.click()
  }

  void clickUnpublishButton() {
    unpublishButton.click()
  }

  void clickLinkButton() {
    linkButton.click()
  }

  void clickDownloadButton() {
    donwloadButton.click()
  }

  void clickDeleteButton() {
    deleteButton.click()
  }

  void clickUploadButton() {
    uploadButton.click()
  }

  // todo click by document name?
  void clickDocument() {
    documentList[0].clickCell()
  }

  void selectNumItems(String numItems) {
    typeDropdown.$('.dropdown-item', text:numItems).click()
  }
}