# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, share, quarter, fiscal, collected) {
  rmarkdown::render(
    here("scripts", "enhanced_sfp_report_share.Rmd"), params = list(
      data = data,
      share = share,
      quarter = quarter,
      fiscal = fiscal,
      collected = collected
    ),
    output_file = paste0("SFP_Enhanced_Report_", share, "_", quarter, "_", fiscal, ".html"),
    output_dir = here("output"),
  )
}

#render, stating parameters
render_report("2022-01-01_ENV_Enhanced_Data.csv", "S40183", "Q4", "FY21-22", "2021-12-22")
