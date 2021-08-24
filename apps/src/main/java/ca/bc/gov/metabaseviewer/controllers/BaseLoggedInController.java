package ca.bc.gov.metabaseviewer.controllers;

import ca.bc.gov.metabaseviewer.services.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;

@Controller
public abstract class BaseLoggedInController {

    @Autowired
    protected UserService userService;

    protected void addCommonUserAttributes(final Model model) {
        model.addAttribute("dashboards", userService.getAvailableDashboards());
    }
}