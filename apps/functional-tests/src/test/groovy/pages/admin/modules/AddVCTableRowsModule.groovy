package Admin.modules

import Admin.modules.VCTableRows
import geb.waiting.WaitTimeoutException


class AddVCTableRows extends VCTableRows {
  static content = {
      name { $('[data-label=Name') }
      description { $('[data-label=Description') }
  }
}