package Pages.Admin

import geb.waiting.WaitTimeoutException

class AddProjectPage extends BaseAppPage {
  static at = {}
  static url = '/projects/add'
  // todo add an edit project page that extends this one, overwrites the expected url, otherwise the same
  // url = '/projects/<some_id>/edit'
  static content = {
    submitButton { $('button[type|="submit"]') }
    cancelButton { $('button[type|="cancel"]') }
    projectName { $('#name') }
    natureDropdown { $('#build') }
    typeDropdown { $('#type') }
    subTypeDropdown { $('#sector') }
    description { $('#description') }
    location { $('#location') }
    lat { $('#lat') }
    lon { $('#long') }
    regionDropDown { $('select[formcontrolname|=region]') }
    regionDropDown { $('select[name|=region]') }
    orgLinkButton { $('#orgLink')}

    // supplementary info
    ceaaDropdown { $('#CEAAInvolvement') }
    ceaaURL { $('#CEAALink') }
    capitalInvest { $('#capital') }
    notes { $('#notes') }
  
    // overall status
    eaStatus { $('#eaStatus') }
    eaStatusDate { $('#eaStatusDate') }
    eaDecisionDat { $('input[name|=decisionDate]') }
    subStartedRadio { $('div[name|=substantially]') }

    // people
    projectLead { $('#projectLead') }
    projectEPD { $('#responsibleEPD') }
  }

  void clickSave() {
    submitButton.click()
  }
  void clickCancel() {
    cancelButton.click()
  }

  void setName(String name) {
    projectName.value(name)
  }

  void selectType(String projType) {
    typeDropdown.$('option', text:projType).click()
  }

  void selectSubType(String subType) {
    subTypeDropdown.$('option', text:subType).click()
  }

  void selectNature(String nature) {
    natureDropdown.$('option', text:nature).click()
  }

  void setDescription(String someText) {
    description.value(someText)
  }

  void setLocation(String address) {
    location.value(address)
  }

  void setLat(String coord) {
    lat.value(coord)
  }

  void setLon(String coord) {
    lon.value(coord)
  }
}