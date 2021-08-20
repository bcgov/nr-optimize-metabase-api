package Pages.Admin

import Admin.modules.WorkingGroupTableRows

class ProjectUpdatesPage extends BaseAppPage {
  static at = {}
  static content = {
    headlineList {
        $('table tr').tail().moduleList(WorkingGroupTableRows) // tailing to skip header row , is necessary?
    }
  }

  void clickHeadline() {
    headlineList[0].clickCell()
  }
}