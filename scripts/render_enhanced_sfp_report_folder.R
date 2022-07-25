# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, ministry, path, folder, quarter, fiscal, collected) {
  rmarkdown::render(
    here("scripts", "enhanced_sfp_report_folder.Rmd"), params = list(
      data = data,
      ministry = ministry,
      path = path,
      folder = folder,
      quarter = quarter,
      fiscal = fiscal,
      collected = collected
    ),
    output_file = paste0("SFP_Enhanced_Report_", ministry, "_", folder, "_", quarter, "_", fiscal, ".html"),
    output_dir = here("output"),
  )
}

#render, stating parameters
render_report("2022-07-01_FOR_SFP_Enhanced_Data.csv", "FOR", "\\\\\\\\KAMSFILE\\\\S63072\\\\ARCH", "ARCH", "Q2", "FY22-23", "2022-06-28")
