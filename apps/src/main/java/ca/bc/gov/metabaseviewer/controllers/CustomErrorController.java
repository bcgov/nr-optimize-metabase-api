package ca.bc.gov.metabaseviewer.controllers;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.web.servlet.error.ErrorController;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

import javax.servlet.RequestDispatcher;
import javax.servlet.http.HttpServletRequest;

@Controller
public class CustomErrorController implements ErrorController {
    private static Logger logger = LoggerFactory.getLogger(CustomErrorController.class);

    @RequestMapping("/error")
    public String handleError(HttpServletRequest request) {
        Object status = request.getAttribute(RequestDispatcher.ERROR_STATUS_CODE);
        Integer statusCode = Integer.valueOf(status.toString());

        return getErrorView(statusCode);
    }

    static String getErrorView(Integer statusCode) {
        if (statusCode != null) {
            HttpStatus statusEnum = null;
            try {
                statusEnum = HttpStatus.valueOf(statusCode);
            } catch (IllegalArgumentException ex) {
                // Unkown error code (should never happen), will fall through null check below and return unknownError
                logger.error(ex.toString());
            }

            if (statusEnum != null) {
                if (statusEnum == HttpStatus.NOT_FOUND) {
                    return "errors/404";
                } else if (statusEnum.is4xxClientError()) {
                    return "errors/4xx";
                } else if (statusEnum.is5xxServerError()) {
                    return "errors/5xx";
                }
            }
        }
        logger.error("handleError > Could not resolve error code into http status and view. Code : {}",
                statusCode == null ? "NULL" : statusCode.toString());
        return "errors/unknownError";
    }

    @Override
    public String getErrorPath() {
        return "/error";
    }
}