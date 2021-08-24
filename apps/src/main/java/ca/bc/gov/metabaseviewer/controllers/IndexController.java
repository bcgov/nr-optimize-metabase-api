package ca.bc.gov.metabaseviewer.controllers;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;

@Controller
public class IndexController {
   Logger logger = LoggerFactory.getLogger(IndexController.class);
	
   @GetMapping(value = "/")
   public String index() {
      logger.info("/");
      return "index";
   }
   
   @GetMapping(path = "/logout")
   public String logout(HttpServletRequest request) throws ServletException {
      logger.info("/logout");
      request.logout();
      return "redirect:/";
   }
}