package ca.bc.gov.metabaseviewer.model.CommonEmailService;

import lombok.Data;

@Data
public class ChesEmailBody {
    private String from;
    private String[] to;
    private String subject;
    private String bodyType;
    private String body;
}
