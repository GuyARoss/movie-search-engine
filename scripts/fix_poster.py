import csv

def fix(affiliation_csv: str, top: str):
    final = []

    with open(affiliation_csv) as csvfile:
        reader = csv.DictReader(csvfile)

        for rr in reader:
            with open(top) as topfile:
                topreader = csv.DictReader(topfile)

                for r in topreader:
                    if rr['Movie Title'] == r['Title']:
                        final.append([
                            rr['ID'], rr['Movie Title'], rr['Year'], rr['Scene Title'], r['Cover URL']
                        ])

    
    with open("movie_scene_affiliation_fix.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Movie Title", "Year", "Scene Title", "Cover URL"])
        writer.writerows(final)


if __name__ == "__main__":
    import sys

    f1 = sys.argv[1]
    f2 = sys.argv[2]
    fix(f1, f2)