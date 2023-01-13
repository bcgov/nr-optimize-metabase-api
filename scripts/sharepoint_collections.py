# SharePoint Collections
auth = "https://sts.gov.bc.ca/adfs/ls?wa=wsignin1.0&wtrealm=urn%3asp.gov.bc.ca&wctx=https%3a%2f%2fnrm.sp.gov.bc.ca%2fsites%2f"

site_collections = {
    "af": auth
    + "AGRI%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FAGRI%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=b1599f7c-dce9-440a-5089-0080010000b7&RedirectToIdentityProvider=AD+AUTHORITY",
    "bcts": auth
    + "BCTS%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FBCTS%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=87d2a718-04fd-43d9-b331-0080010400db&RedirectToIdentityProvider=AD+AUTHORITY",
    "bcws": auth
    + "Wildfire%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FWILDFIRE%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=ea8dbfe5-a803-4de6-41bd-0080010000c6&RedirectToIdentityProvider=AD+AUTHORITY",
    "crts": auth
    + "CRTS%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FCRTS%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=907d272e-56b2-4116-5a95-0080010400ea&RedirectToIdentityProvider=AD+AUTHORITY",
    "eao": auth
    + "EAO%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FEAO%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=66dc3ac6-7e51-4897-4ce7-008001000030&RedirectToIdentityProvider=AD+AUTHORITY",
    "emli": auth
    + "EMPR%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FEMPR%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=8541b346-e768-452b-4bba-00800100002d&RedirectToIdentityProvider=AD+AUTHORITY",
    "env": auth
    + "ENV%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FENV%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=15460ce6-01a4-4083-b51d-0080000000bd&RedirectToIdentityProvider=AD+AUTHORITY",
    "for1": auth
    + "flnr%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FFLNR%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=243e6be9-e8b8-466f-ce8e-00800100008f&RedirectToIdentityProvider=AD+AUTHORITY",
    "for2": auth
    + "FLNR2%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FFLNR2%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=d53ecc37-da64-4797-4d43-008001000001&RedirectToIdentityProvider=AD+AUTHORITY",
    "irr": auth
    + "IRR%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FIRR%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=935d16a0-f66c-466b-f991-0080010400f1&RedirectToIdentityProvider=AD+AUTHORITY",
    "irrcs": auth
    + "irrcs%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FIRRCS%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=303265df-c6b6-434d-feab-0080010400ce&RedirectToIdentityProvider=AD+AUTHORITY",
    "nrm": auth
    + "NRM%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FNRM%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=ea5d285a-f056-4a04-00bd-0080010400d1&RedirectToIdentityProvider=AD+AUTHORITY",
}
