package ca.bc.gov.metabaseviewer.model.CommonEmailService;

import lombok.Data;

@Data
public class Message {
    private String msgId;
    private String[] to;
}
