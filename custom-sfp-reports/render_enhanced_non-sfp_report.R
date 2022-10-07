# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, businessarea, path, folder, san_tier, collected) {
  rmarkdown::render(
    here("scripts", "enhanced_non-sfp_report.Rmd"), params = list(
      data = data,
      businessarea = businessarea,
      path = path,
      folder = folder,
      san_tier = san_tier,
      collected = collected
    ),
    output_file = paste0("Non-SFP_Custom_Report_", folder, "_", businessarea, "_", collected, ".html"),
    output_dir = here("output"),
  )
}

#render, stating parameters
render_report("2022-09-22_BCWS_Training_Enhanced_Report.csv", "BCWS", "E:////PROV////Documents////Training", "Training", 2, "2022-09-22")
