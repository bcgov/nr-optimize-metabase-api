# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, ministry, path, folder, quarter, fiscal, collected) {
  rmarkdown::render(
    here("scripts", "enhanced_sfp_report_folder_v2.Rmd"), params = list(
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

#render, stating parameters and remembering to escape any special characters in the pathname
render_report("2022-10-01_ENV_SFP_Enhanced_Data.csv", "ENV", "/ifs/sharedfile/top_level/C40/S40086/WANSHARE/ROB", "ROB", "Q3", "FY22-23", "2022-09-29")
