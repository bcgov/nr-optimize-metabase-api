package ca.bc.gov.metabaseviewer.controllers;

import ca.bc.gov.metabaseviewer.model.Dashboard;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.ArrayList;

@Controller
public class DashboardController extends BaseLoggedInController {
    Logger logger = LoggerFactory.getLogger(DashboardController.class);

    @GetMapping(path = "/sec/dashboard")
    public String getDashboardHome(Model model) {
        logger.info("/dashboard");
        addCommonUserAttributes(model);
        return "welcome";
    }

    @GetMapping(path = "/sec/dashboard/{metabaseId}")
    public String getDashboard(@PathVariable(name = "metabaseId") Integer metabaseId, Model model) {
        logger.info("/dashboard/{}", metabaseId);
        addCommonUserAttributes(model);

        // Is this user allowed to access the dashboard from the URL (if they direct accessed the URL)
        // Get allowed dashboards out of the model since they've already been calculated in the base class
        userService.checkDashboardAllowed(metabaseId, (ArrayList<Dashboard>) model.asMap().get("dashboards"));

        try {
            model.addAttribute("iframeUrl", userService.getDashboard(metabaseId));
        } catch (Exception ex) {
            logger.error("/dashboard error occurred. Ex: {}", ex.toString());
            model.addAttribute("error", "An error occurred while attempting to fetch the dashboard.");
        }
        return "dashboard";
    }
}