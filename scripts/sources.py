import pandas as pd


def get_sample_data():

    data = {

        "city":[
            "Toronto",
            "Ottawa",
            "Thunder Bay"
        ],

        "region":[
            "GTA",
            "East",
            "North"
        ],

        "average_house_price":[
            1030000,
            650000,
            430000
        ],

        "average_rent":[
            2750,
            2100,
            1450
        ],

        "median_income":[
            95000,
            102000,
            76000
        ],

        "latitude":[
            43.6532,
            45.4215,
            48.3809
        ],

        "longitude":[
            -79.3832,
            -75.6972,
            -89.2477
        ]

    }

    return pd.DataFrame(data)