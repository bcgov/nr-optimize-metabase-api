package Pages.Admin

import Pages.Admin.BaseAppPage

class CreateProjectGroupModal extends BaseAppPage {
  static at = { pageTitle.text() == 'Add Group' }
  static content = {
    // todo revisit this selector
    modalSelector(wait:true) { $('.modal-open .day-calculator') }

    pageTitle { modalSelector.$('.modal-header h2') }

    yesButton { modalSelector.$('.modal-footer .btn btn-success') }
    cancelButton { modalSelector.$('.modal-footer .btn btn-primary') }
    closeButton { modalSelector.$('.close-btn') }
    inputName { modalSelector.$('input[name|=groupNameField]') }
  }

  void setGroupName(String name) {
    inputName.value(name)
  }

  void clickSave() {
    yesButton.click()
  }

  void clickCancel() {
    cancelButton.click()
  }

  void clickClose() {
    closeButton.click()
  }
}