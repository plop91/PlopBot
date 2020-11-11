import json


def readToken(filename):
    with open(filename, "r") as f:
        temp_token = f.readlines()
        f.close()
        return temp_token[0].strip()


def readJson(filename):
    with open(filename) as f:
        data = json.load(f)
        f.close()
        return data


def addToJson(filename, json_data, tag, data):
    with open(filename, "w") as file:
        json_data[tag].append(data)
        json.dump(json_data, file, indent=4)
