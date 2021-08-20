package Pages.Admin

import Pages.Admin.AddProjectPage
import geb.waiting.WaitTimeoutException

class EditProjectPage extends AddProjectPage {
  // todo is this even needed? or will tests navigate here through links
  // leaning towards the latter
  static url = '/projects/<some_id>/edit'
}