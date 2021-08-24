package ca.bc.gov.metabaseviewer.controllers;

import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
@SpringBootTest
public class CustomErrorControllerTests {

    @Test
    public void getErrorPath() {
        CustomErrorController ctrl = new CustomErrorController();
        Assert.assertEquals("/error", ctrl.getErrorPath());
    }

    private static final String ERR_UN = "errors/unknownError";
    private static final String ERR_404 = "errors/404";
    private static final String ERR_4xx = "errors/4xx";
    private static final String ERR_5xx = "errors/5xx";

    @Test
    public void getErrorView() {
        Assert.assertEquals(ERR_404, CustomErrorController.getErrorView(404));
        Assert.assertEquals(ERR_4xx, CustomErrorController.getErrorView(401));
        Assert.assertEquals(ERR_5xx, CustomErrorController.getErrorView(500));
        Assert.assertEquals(ERR_5xx, CustomErrorController.getErrorView(503));
    }

    @Test
    public void getErrorViewUnknown() {
        Assert.assertEquals(ERR_UN, CustomErrorController.getErrorView(888));
        Assert.assertEquals(ERR_4xx, CustomErrorController.getErrorView(499));
        Assert.assertEquals(ERR_UN, CustomErrorController.getErrorView(null));
    }
}