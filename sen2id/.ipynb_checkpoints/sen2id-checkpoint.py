import ee
import pystac_client

def match_id(product_id, source = "pc"):

    # PRODUCT_ID (GEE)
    # "S2A_MSIL2A_20210605T153621_N0500_R068_T18NUK_20230130T105832"

    # id (Planetary Computer)
    # "S2A_MSIL2A_20210605T153621_R068_T18NUK_20210606T054007"

    idx = {
        "date": {"ee": 2, "pc": 2},
        "orbit": {"ee": 4, "pc": 3},
        "MGRS": {"ee": 5, "pc": 4},
    }

    split_id = product_id.split("_")

    date_original = split_id[idx["date"][source]]
    date = f"{date_original[:4]}-{date_original[4:6]}-{date_original[6:8]}"

    orbit_original = split_id[idx["orbit"][source]]
    orbit = int(orbit_original[1:])

    MGRS_original = split_id[idx["MGRS"][source]]
    MGRS = MGRS_original[1:]
    
    components_ee = {
        "SENSING_ORBIT_NUMBER": orbit,
        "MGRS_TILE": split_id[idx["MGRS"][source]][1:],
    }

    components_pc = {
        "sat:relative_orbit": orbit,
        "s2:mgrs_tile": split_id[idx["MGRS"][source]][1:],
    }

    return {
        "product_id": product_id,
        "source": source,
        "date": date,
        "date_str": date_original,
        "orbit_str": orbit_original,
        "MGRS_str": MGRS_original,
        "ee": components_ee,
        "pc": components_pc
    }

def match_ids(product_ids, source = "pc"):
    return [match_id(i, source = source) for i in product_ids]

def get_stac_filter(product_ids):

    if isinstance(product_ids, str):
        product_ids = [product_ids]
    
    matches = match_ids(product_ids, source = "ee")

    args = []
    
    for match in matches:

        date = match["date_str"]
        orbit = match["orbit_str"]
        MGRS = match["MGRS_str"]

        arg = {
            "op": "like",
            "args": [ { "property": "id" }, f"%{date}%{orbit}%{MGRS}%" ]
          }

        args.append(arg)
    
    filter_pc = {
        "op": "or",
        "args": args
      }
    
    return filter_pc

def from_ee_to_pc(image_collection = None,product_ids = None):

    CATALOG = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

    if (image_collection is None) and (product_ids is None):
        raise Exception("One of 'image_collection' or 'product_ids' must be provided!")

    if isinstance(image_collection, ee.ImageCollection):
        product_ids = image_collection.aggregate_array("PRODUCT_ID").getInfo()
    
    SEARCH = CATALOG.search(
        collections=["sentinel-2-l2a"],
        filter=get_stac_filter(product_ids)
    )

    return SEARCH

    