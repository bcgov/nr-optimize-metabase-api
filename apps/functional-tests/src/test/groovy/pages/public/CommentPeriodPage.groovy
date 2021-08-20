package Pages.Public

class CommentPeriodPage extends BaseAppPage {
  static content = {
    pageTitle { $('h1') }
    commentPeriodStatus { $('#cp-status') }
    commentPeriodDate { $('#cp-date') }
    submitComment { $('#submit-c') }
    backButton { $('#back') }
    noComments { $('#empty') }
  }
}