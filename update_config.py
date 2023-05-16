import json, sys

lifetime = sys.argv[1]
print(lifetime)
with open("config.json", "r") as jsonFile:
    data = json.load(jsonFile)

data["LIFE_TIME"] = lifetime

with open("config.json", "w") as jsonFile:
    json.dump(data, jsonFile)

