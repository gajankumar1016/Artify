import urllib.request, json
import csv
import time

"""Note: The url server might not respond because of url server request limits
on the free trial use of this API. In such a case, simply wait about 5 seconds
and press 'ctrl' + C ONCE and the adding of artworks should result"""

# Use this to specify how many additional paintings you want (for now, I've only added 30
# for git's sake)
num_artworks = 30

if last_j == 0:
    f = open("artinfo.csv", "w")
    f.truncate()
    f.close()

    with open('artinfo.csv', mode='a') as art_file:
        art_adder = csv.writer(art_file, delimiter='|', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        art_adder.writerow(["Id", "FileName", "Title", "Artist", "Year", "Country", "Style", "Link"])



# Top 600 most visited paintings
art_url = "https://www.wikiart.org/en/App/Painting/MostViewedPaintings?offset=0&quantity=100&limit=100&randomSeed=123&json=2"


with urllib.request.urlopen(art_url) as url:
    data = json.loads(url.read().decode())

# Making sure the API's 'style' attribute matches Gajan's model for similarity exactly
case_match = {"Art Nouveau (Modern)":"Art_Nouveau_Modern", "Post-Impressionism":"Post_Impressionism", "Abstract Expressionism":"Abstract_Expressionism", "Northern Renaissance":"Northern_Renaissance", "Naïve Art (Primitivism)":"Naive_Art_Primitivism"}

def normalizeStyle(wiki_style):
    if wiki_style in case_match.keys():
        return case_match[wiki_style]
    else:
        return wiki_style

i = 0
for j in range(min(num_artworks, len(data))):
    art = data[j]

    if j == 3:
        continue

    # Additional info including style of painting and location of creation
    painting_url = "http://www.wikiart.org/en/App/Painting/ImageJson/" + str(art['contentId'])

    with urllib.request.urlopen(painting_url) as url:
        art_info = json.loads(url.read().decode())

    image_path = str(i + 1) + ".jpg"


    try:
        print("last j: " + str(j) + "; last i: " + str(i))
        urllib.request.urlretrieve(art['image'], "../devimages/" + image_path)
    except:
        print("Ran into an error, continue...")
        continue

    with open('artinfo.csv', mode='a') as art_file:
        art_adder = csv.writer(art_file, delimiter='|', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        art_adder.writerow([i + 1, image_path, art['title'], art['artistName'], art['completitionYear'], art_info['location'], normalizeStyle(art_info['style']), art['image']])


    print("adding...")
    print(art['title'])
    print(art['artistName'])
    print(normalizeStyle(art_info['style']))
    print(art['completitionYear'])
    print("----------")
    i += 1
