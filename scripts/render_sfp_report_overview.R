# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, ministry, quarter, fiscal, collected) {
  rmarkdown::render(
    here("scripts", "sfp_report_overview.Rmd"), params = list(
      data = data,
      ministry = ministry,
      quarter = quarter,
      fiscal = fiscal,
      collected = collected
    ),
    output_file = paste0("SFP_Enhanced_Report_", ministry, "_", quarter, "_", fiscal, ".html"),
    output_dir = here("output"),
  )
}

#render, stating parameters
render_report("2022-01-01_FLNR_Enhanced_Data.csv", "FLNR", "Q4", "FY21-22", "2021-12-22")
