def assign_div_acronyms(df, min_short, min_dict):
    df.loc[df["Ministry"] == min_short, "Div_Acronym"] = (
        df["Division"]
        .str.extract(fr"({'|'.join(min_dict.keys())})", expand=False)
        .map(min_dict)
    )


def get_div_acronym(div_name, min_dict):
    return min_dict[div_name]
