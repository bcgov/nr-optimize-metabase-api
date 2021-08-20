package Pages.Admin

import Admin.modules.ContactsTableRows
import Pages.Admin.ProjectGroupsPage

class GroupContactsPage extends ProjectGroupsPage {
  static at = { pageTitle.text() == 'Name of Group' }
  static content = {
    //groups
    pageTitle { $('label[for|=title]') }
    saveButton { $('#button-s') }
    backButton { $('#button-cl') }
    nameInput { $('#nameInput') }

    //add contacts 
    contactList {
        $('table tr').tail().moduleList(ContactsTableRows) // tailing to skip header row 
    }
    searchInput { $('#keywordInput') }
    searchButton { $('#search') }
    createNewContact { $('#button-cc')}
  }

  void clickSave() {
    saveButton.click()
  }

  void setGroupName(String name) {
    nameInput.value(name)
  }

  void clickBackButton() {
    backButton.click()
  }

  void setSearchTerms(String contact) {
    searchInput.value(contact)
  }

  void clickSearch() {
    searchButton.click()
  }

  void clickNewContact() {
    createNewContact.click()
  }

  void clickContact() {
    contactList[0].clickCell()
  }

}