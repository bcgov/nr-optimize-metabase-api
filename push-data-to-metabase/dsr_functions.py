def assign_div_acronyms(df, min_short, min_dict):
    df.loc[df["Ministry"] == min_short, "Div_Acronym"] = (
        df["Division"]
        .str.extract(fr"({'|'.join(min_dict.keys())})", expand=False)
        .map(min_dict)
    )
