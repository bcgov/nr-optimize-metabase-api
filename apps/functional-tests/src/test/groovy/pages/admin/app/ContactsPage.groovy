package Pages.Admin

import Admin.modules.ContactsTableRows

class ContactsPage extends BaseAppPage {
  static at = {}
  static content = {
    newContactButton { $('#add-contact') }
    contactList {
        $('table tr').tail().moduleList(ContactsTableRows) // tailing to skip header row 
    }
  }

  void clickNewContact() {
    newContactButton.click()
  }

  void clickEditContact() {
    contactList[0].clickAction()
  }

}
