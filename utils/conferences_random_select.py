from random import randint

with open("conferences.csv") as file:
    confs = [line.strip().split(",") for line in file.readlines()]

conferences = []
years = []

for line in confs:
    conferences.append(line[0].lower())
    years.append(line[1:][randint(0,len(line[1:])-1)])

print(conferences)
print(years)
