package ca.bc.gov.metabaseviewer.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

// Our custom forbidden access exception
@ResponseStatus(value = HttpStatus.FORBIDDEN, reason = "User tried to go to a resource they don't have access to")
public class NrUnauthorizedException extends RuntimeException {
}
