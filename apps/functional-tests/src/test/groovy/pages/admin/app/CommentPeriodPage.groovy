package Pages.Admin

import Admin.modules.CommentTableRows
import geb.waiting.WaitTimeoutException

class CommentPeriodPage extends BaseAppPage {
  static content = {
    title { $('.container-fluid-padding h1') }
    detailsTab { $('#mat-tab-label-0-0') }
    reviewTab { $('#mat-tab-label-0-1') }
    actionDropDown { $('#actionDropDown') }

    dateRange { $('.date-range') }
    publishState { $('#publish-state') }
    cpStatus { $('#status') }
    milestone { $('#milestone') }
    instrucstions { $('#instructions') }
    commentsReceivedSection { $('#comments-received-details') }

    // filters, select by label text value
    commentList {
      // todo update this selector
      $('table tr').tail().moduleList(CommentTableRows) // tailing to skip header row 
    }
  }

  void clickDetailsTab() {
    detailsTab.click()
  }

  void clickReviewTab() {
    reviewTab.click()
  }
}