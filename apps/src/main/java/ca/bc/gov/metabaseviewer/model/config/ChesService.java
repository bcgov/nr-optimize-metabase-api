package ca.bc.gov.metabaseviewer.model.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "chesservice")
public class ChesService {
    private String auth;
    private String client;
    private String secret;
    private String emailEndpoint;
    private String emailAddress;
}
