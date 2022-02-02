# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, path, folder, quarter, fiscal, collected) {
  rmarkdown::render(
    here("scripts", "enhanced_sfp_report_folder.Rmd"), params = list(
      data = data,
      path = path,
      folder = folder,
      quarter = quarter,
      fiscal = fiscal,
      collected = collected
    ),
    output_file = paste0("SFP_Enhanced_Report_", folder, "_", quarter, "_", fiscal, ".html"),
    output_dir = here("output"),
  )
}

#render, stating parameters
render_report("2021-04-01_ENV_SFP_Enhanced_Data.csv", "^\\\\\\\\SLEDGE\\\\S40203\\\\IRMT", "IRMT", "Q1", "FY21-22", "2021-04-27")

