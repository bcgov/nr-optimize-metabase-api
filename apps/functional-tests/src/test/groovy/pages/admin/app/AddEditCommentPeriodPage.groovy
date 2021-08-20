package Pages.Admin

import geb.waiting.WaitTimeoutException

class AddEditCommentPeriodPage extends BaseAppPage {
  static content = {
    dateStart { $('#inputStartDate') }
    dateEnd { $('#inputEndDate') }
    publishStateDropDown { $('#publishedState') }
    information { $('#infoForComment') }
    description { $('#description') }
    cpStatus { $('#status') }
    milestoneDropDown { $('select[formcontrolname=milestoneSel') }

    openHouseDate { $('#inputOpenHouseDate') }
    openHouseDescription { $('#openHouseDescription') }

    cancelButton { $('button[type=cancel]') }
    submitButton { $('button[type=submit]') }
  }

  Date currDate = new Date().format('yyyy-mm-dd')
  void setStartDateFuture() {
    dateStart.value(currDate + 7)
  }

  void setEndDateFuture() {
    dateEnd.value(currDate + 14)
  }

  void setStartDateNow() {
    // currdate
    dateStart.value(currDate)
  }

  void setEndDateNow() {
    dateEnd.value(currDate + 7)
  }

  void enterInformation(String info) {
    information.value(info)
  }

  void enterDescription(String desc) {
    description.value(desc)
  }
  void selectPublishState(String action) {
    publishStateDropdown.$('.dropdown-item', text:action).click()
  }

  void selectMilestone(String action) {
    milestoneDropdown.$('.dropdown-item', text:action).click()
  }

  void setDateOpenHouse() {
    // to start date?
  }

  void setOHDescription(String desc) {
    openHouseDescription.value(desc)
  }

  void clickSave() {
    submitButton.click()
  }

  void clickCancel() {
    cancelButton.click()
  }
}