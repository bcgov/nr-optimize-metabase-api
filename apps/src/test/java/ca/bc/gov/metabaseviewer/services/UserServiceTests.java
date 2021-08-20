package ca.bc.gov.metabaseviewer.services;

import ca.bc.gov.metabaseviewer.exception.NrUnauthorizedException;
import ca.bc.gov.metabaseviewer.model.Dashboard;
import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.ArrayList;
import java.util.List;

@RunWith(SpringRunner.class)
@SpringBootTest
public class UserServiceTests {
    @Test
    public void dashJson() {
        Assert.assertEquals("{\"resource\": {\"dashboard\": 2}, \"params\": {}}", UserService.dashJson(2));
    }

    @Test
    public void checkDashboardAllowed() {
        List<Dashboard> sampleList = new ArrayList<>();
        sampleList.add(new Dashboard("test", 3));
        sampleList.add(new Dashboard("test", 2));
        UserService.checkDashboardAllowed(2, sampleList);
    }

    @Test(expected = NrUnauthorizedException.class)
    public void checkDashboardAllowedFails() {
        List<Dashboard> sampleList = new ArrayList<>();
        sampleList.add(new Dashboard("test", 3));
        sampleList.add(new Dashboard("test", 4));
        UserService.checkDashboardAllowed(2, sampleList);
    }

    @Test(expected = NrUnauthorizedException.class)
    public void checkDashboardAllowedFailsEmpty() {
        List<Dashboard> empty = new ArrayList<>();
        UserService.checkDashboardAllowed(2, empty);
    }
}
