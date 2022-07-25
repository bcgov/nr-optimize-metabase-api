# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, ministry, share, quarter, fiscal, collected) {
  rmarkdown::render(
    here("scripts", "enhanced_sfp_report_share.Rmd"), params = list(
      data = data,
      ministry = ministry,
      share = share,
      quarter = quarter,
      fiscal = fiscal,
      collected = collected
    ),
    output_file = paste0("SFP_Enhanced_Report_", ministry, "_", share, "_", quarter, "_", fiscal, ".html"),
    output_dir = here("output"),
  )
}

#render, stating parameters
render_report("2022-07-01_FOR_SFP_Enhanced_Data.csv", "FOR", "S63110", "Q2", "FY22-23", "2022-06-28")
