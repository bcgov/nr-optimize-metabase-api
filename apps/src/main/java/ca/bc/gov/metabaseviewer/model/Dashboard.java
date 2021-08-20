package ca.bc.gov.metabaseviewer.model;

import lombok.Data;

@Data
public class Dashboard {
    private final String displayName;
    private final int metabaseId;
    private boolean currentlySelected = false;
}
