#!/usr/bin/env python3

import yaml

with open('services.yaml') as f:
    docs = yaml.load_all(f, Loader=yaml.Loader)

    for doc in docs:
        for k, v in doc.items():
            print(k, "->", v)

print( doc["name"])
print( doc["procman"]["java"])
print( doc["procman"]["java"]["args"][0])
