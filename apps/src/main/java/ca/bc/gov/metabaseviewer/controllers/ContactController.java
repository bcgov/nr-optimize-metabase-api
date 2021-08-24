package ca.bc.gov.metabaseviewer.controllers;

import ca.bc.gov.metabaseviewer.model.CommonEmailService.ChesEmailBody;
import ca.bc.gov.metabaseviewer.model.CommonEmailService.ChesEmailResponse;
import ca.bc.gov.metabaseviewer.model.config.ChesService;
import ca.bc.gov.metabaseviewer.model.ContactForm;
import ca.bc.gov.metabaseviewer.model.TokenResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.client.RestTemplate;

import java.security.Principal;

@Controller
public class ContactController extends BaseLoggedInController {
    Logger logger = LoggerFactory.getLogger(ContactController.class);

    @Autowired
    private ChesService chesProperties;

    @GetMapping(path = "/sec/contact")
    public String getContact(Principal principal, Model model) {
        addCommonUserAttributes(model);
        ContactForm contactForm = new ContactForm();
        contactForm.setEmail(userService.getUserDetails(principal).getEmail());
        model.addAttribute("contactForm", contactForm);

        return "contact";
    }

    @PostMapping("/sec/contact")
    public String contactSubmit(@ModelAttribute ContactForm contactForm, Model model) {
        // TODO: to go to a service class and split to methods
        try {
            //Get a Token. If this is used anywhere else in this application, this code should be centralized. But since
            //this is the only spot we do a call to the common service, just get the token here,
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
            headers.setBasicAuth( chesProperties.getClient(), chesProperties.getSecret() );

            MultiValueMap<String, String> map= new LinkedMultiValueMap<>();
            map.add("grant_type", "client_credentials");
            HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(map, headers);

            RestTemplate restTemplate = new RestTemplate();
            logger.debug("fetching token. auth endpoint: {}", chesProperties.getAuth());
            ResponseEntity<TokenResponse> response = restTemplate.postForEntity( chesProperties.getAuth(), request , TokenResponse.class );
            addCommonUserAttributes(model);

            String token = response.getBody().getAccess_token();
            logger.debug("token: {}", token);

            ChesEmailBody email = new ChesEmailBody();
            email.setFrom(contactForm.getEmail());
            email.setBody(contactForm.getBody());
            email.setBodyType("text");
            email.setSubject(contactForm.getInquiry());
            String[] to = {chesProperties.getEmailAddress()};
            email.setTo(to);

            HttpHeaders emailHeaders = new HttpHeaders();
            emailHeaders.setBearerAuth(token);
            emailHeaders.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<ChesEmailBody> emailEntity = new HttpEntity<>(email , emailHeaders);
            logger.debug("Calling CHES");
            ResponseEntity<ChesEmailResponse> emailResponse = restTemplate.postForEntity( chesProperties.getEmailEndpoint(), emailEntity , ChesEmailResponse.class );

            if(emailResponse.getStatusCodeValue() != 201) {
                throw new Exception("Response from CHES api was not a 201. Response: " + emailResponse.toString());
            }
            addCommonUserAttributes(model);
            model.addAttribute("txId", emailResponse.getBody().getTxId());
            return "contactSuccess";

        } catch (Exception ex) {
            logger.error("contactSubmit > failed to send email for contact form info: {}. Exception: {}", contactForm.toString(), ex.toString());
            return "errors/contactFailure";
        }

    }
}