package ca.bc.gov.metabaseviewer.model.CommonEmailService;

import lombok.Data;

@Data
public class ChesEmailResponse {
    private String txId;
    private Message[] Messages;
}
