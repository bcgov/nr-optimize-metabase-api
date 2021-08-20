package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException


class ContactsTableRows extends Module {
  static content = {
      select { $('[data-label=Select]') }
      name { $('[data-label=Name]') }
      organization { $('[data-label=Organization]')}
      email { $('[data-label=Email]') }
      phoneNum { $('[data-label=Phone]') }
      edit { $('[data-label=Event]') } //All contacts table only
  }

  void clickCell() {
      name.click()
  }

  void clickAction() {
    edit.click()
  }
}