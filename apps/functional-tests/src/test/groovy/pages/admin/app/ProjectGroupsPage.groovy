package Pages.Admin

import Admin.modules.WorkingGroupTableRows
import Pages.Admin.BaseAppPage
import geb.waiting.WaitTimeoutException

class ProjectGroupsPage extends BaseAppPage {
  static at = {}
  static content = {
    selectAllButton { $('#button-sa') }
    addButton { $('#button-a') }
    editButton { $('#button-e') }
    deleteButton { $('#button-d') }
    exportButton { $('#button-ex') }
    copyEmailsButton { $('#button-ce') }
    workingGroupList {
        $('table tr').tail().moduleList(WorkingGroupTableRows) // tailing to skip header row 
    }
  }
  
  void clickWorkingGroup() {
    workingGroupList[0].clickCell()
  }

  void selectAll() {
    selectAllButton.click()
  }

  void addGroup() {
    addButton.click()
  }

  void editGroup() {
    editButton.click()
  }

  void deleteGroup() {
    deleteButton.click()
  }

  void exportGroup() {
    exportButton.click()
  }

  void copyEmails() {
    copyEmailsButton.click()
  }
}