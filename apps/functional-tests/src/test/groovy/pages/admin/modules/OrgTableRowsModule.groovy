package Admin.modules

import geb.Module

class OrgTableRows extends Module {
  static content = {
    orgName { $('[data-label=Name]') }
    orgType { $('[data-label=Organization]') }
    legal { $('#legal') }
    edit { $('[data-label=Event]') }
  }

  void clickEdit() {
    edit.click()
  }
}