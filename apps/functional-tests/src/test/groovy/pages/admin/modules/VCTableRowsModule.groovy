package Admin.modules

import geb.Module
import geb.waiting.WaitTimeoutException

class VCTableRows extends Module {
  static content = {
      title = { $('[data-label=Title')}
      type { $('[data-label=Type') }
      pillar { $('[data-label=Pillar') }
      parent { $('[data-label=Parent') }
  }

  void clickCell() {
      pillar.click()
  }
}