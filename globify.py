import csv
import json
import traceback
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="ICO Analysis")

data, temp = [], []
countries = {}

def geocode():
    with open("ICO Analysis - ICO Analysis Scraper Analysis.csv", 'r') as csvfile:
        fieldnames = ("Name", "Token", "Type", "Status", "ICO start", "ICO end", "Raised", "Price", "Bonus", "Bounty",
                      "MVP/Prototype", "Platform", "Accepting", "Minimum investment", "Soft cap", "Hard cap", "Country",
                      "Whitelist/KYC", "Restricted areas", "Rate (Overall)", "Benchy Rating", "Benchy Weight",
                      "Expert Team", "Expert Vision", "Expert Product", "Weight of Experts", "Number of Experts",
                      "Expert 1 Team", "Expert 1 Vision", "Expert 1 Product", "Expert 1 Weight", "Expert 2 Team",
                      "Expert 2 Vision", "Expert 2 Product", "Expert 2 Weight", "Expert 3 Team", "Expert 3 Vision",
                      "Expert 3 Product", "Expert 3 Weight", "Expert 4 Team", "Expert 4 Vision", "Expert 4 Product",
                      "Expert 4 Weight", "Expert 5 Team", "Expert 5 Vision", "Expert 5 Product", "Expert 5 Weight",
                      "Expert 6 Team", "Expert 6 Vision", "Expert 6 Product", "Expert 6 Weight", "Expert 7 Team",
                      "Expert 7 Vision", "Expert 7 Product", "Expert 7 Weight", "Expert 8 Team", "Expert 8 Vision",
                      "Expert 9 Product", "Expert 9 Weight", "Expert 10 Team", "Expert 10 Vision", "Expert 10 Product",
                      "Expert 10 Weight", "Expert 11 Team", "Expert 11 Vision", "Expert 11 Product", "Expert 11 Weight",
                      "Expert 12 Team", "Expert 12 Vision", "Expert 12 Product", "Expert 12 Weight", "Expert 13 Team",
                      "Expert 13 Vision", "Expert 13 Product", "Expert 13 Weight", "Expert 14 Team", "Expert 14 Vision",
                      "Expert 14 Product", "Expert 14 Weight", "Expert 15 Team", "Expert 15 Vision",
                      "Expert 15 Product", "Expert 15 Weight", "Expert 16 Team", "Expert 16 Vision",
                      "Expert 16 Product", "Expert 16 Weight", "Expert 17 Team", "Expert 17 Vision",
                      "Expert 17 Product", "Expert 17 Weight", "Expert 18 Team", "Expert 18 Vision",
                      "Expert 19 Product", "Expert 19 Weight", "Expert 20 Team", "Expert 20 Vision",
                      "Expert 20 Product", "Expert 20 Weight")
        reader = csv.DictReader(csvfile, fieldnames)
        next(reader, None)  # skip the headers
        for row in reader:
#            print(json.dump(row))
#            json.dump(row, jsonfile)
#            jsonfile.write('\n')
            try:
                if not row["Country"]:
                    row["Country"] = "Antarctica"
                location = geolocator.geocode(row["Country"])

                if row["Country"] not in countries:
                    countries[row["Country"]] = 1
                else:
                    countries[row["Country"]] += 1

                temp = (location.latitude, location.longitude, countries[row["Country"]])
                print(temp)
                data.append(temp)
            except:
                traceback.print_exc()
                continue

        for country in countries:
            print(country)
            location = geolocator.geocode(country)
            data = (location.latitude, location.longitude, country)
            print(data)
'''


'''
var data = [
    [
    'seriesA', [ latitude, longitude, magnitude, latitude, longitude, magnitude, ... ]
    ],
    [
    'seriesB', [ latitude, longitude, magnitude, latitude, longitude, magnitude, ... ]
    ]
];
'''

geocode()