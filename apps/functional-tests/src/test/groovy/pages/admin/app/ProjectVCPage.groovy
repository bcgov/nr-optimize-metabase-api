package Pages.Admin

import Admin.modules.VCTableRows
import Admin.modules.AddVCTableRows

class ProjectVCPage extends BaseAppPage {
  // todo have at read the breadrumb?
  static at = {}
  static content = {
    addVCButton = { $('#button-a') }
    selectAllButton = { $('#button-sa') }
    deleteButton = { $('#button-d') }
    cancelButton = { $('#button-c') }
    saveButton = { $('#button-s') }

    vcList = { 
      $('table tr').tail().moduleList(VCTableRows) // tailing to skip header row 
    }
    addVCList = {
      $('table tr').tail().moduleList(AddVCTableRows)
    }
  }

  void clickAdd() {
    addVCButton.click()
  }

  void clickSelectAll() {
    selectAllButton.click()
  }

  void clickDelete() {
    deleteButton.click()
  }

  void clickCancel() {
    cancelButton.click()
  }

  void clickSave() {
    saveButton.click()
  }

  void clickVC() {
    vcList[0].clickCell()
  }

  void addVC() {
    addVCList[0].clickCell()
  }
}