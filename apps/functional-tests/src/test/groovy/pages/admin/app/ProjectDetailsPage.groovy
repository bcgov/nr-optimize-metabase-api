package Pages.Admin

import geb.waiting.WaitTimeoutException

class ProjectDetailsPage extends BaseAppPage {
  static at = {}

  static content = {
    // basic info
    proponentText { $('#proponent') }
    natureText { $('#nature') }
    typeText { $('#type') }
    subTypeText { $('#subtype') }
    descriptionText { $('#description') }
    locationText { $('#location') }
    region { $('#region') }
    lat { $('#lat') }
    lon { $('#lon') }

    // supplmentary
    ceaa { $('#ceaa') }
    ceaaUrl { $('#ceaa-url') }
    eaDecision { $('#ea') }
    capital { $('#capital') }
    notes { $('#notes') }

    // status
    eaReadiness { $('#eaReady') }
    activeStatus { $('#active-status') }
    eacStatus { $('#eac-status') }
    substantially { $('#substantially') }



  }
}