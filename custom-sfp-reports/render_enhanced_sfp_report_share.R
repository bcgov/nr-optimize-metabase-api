# setup
library(here)
library(rmarkdown)

# function to render parameters and save html output to file
render_report = function(data, ministry, share, quarter, fiscal, collected) {
  rmarkdown::render(
    here("scripts", "enhanced_sfp_report_share_v2.Rmd"), params = list(
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
render_report("2022-10-01_EMLI_SFP_Enhanced_Data.csv", "EMLI", "S6217", "Q3", "FY22-23", "2022-09-29")
