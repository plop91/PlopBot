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
