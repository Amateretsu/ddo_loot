from bs4 import BeautifulSoup
from dotenv import dotenv_values
import requests, sys, json, mysql.connector, configparser
import tools.normalization_mapping as normalization_mapping

def getSource(inputUrl:str):
    print(f"Collecting HTML from {inputUrl}...")
    html = requests.get(inputUrl) # Request HTML from URL
    sourceCode = BeautifulSoup(html.content, 'html.parser') # Parse HTML
    return sourceCode

def removeTooltip(object:object) -> object:
    if (object.find("span",{"class":"tooltip"})):
        for span in object.find_all("span",{"class":"tooltip"}): # Find all tooltip class spans
            span.decompose() # Delete the tooltip span element
    return object

def feytwistedCleanse(object:object) -> object:
    if (object.find("a",{"title":"Feytwisted"})):
        object.find("br").insert_after("\n")
    return object

def toText(object:object) -> str:
    removeTooltip(object)
    feytwistedCleanse(object)
    text = object.text.strip()
    text = text.replace("\u00a0"," ").replace("\u2014", "-")
    return text

def getListItems(object:object, list:list, cnt:int) -> object:
    tmp_list = []
    cnt += 1
    for li in object.find_all("li",recursive=False):
        if (li.find_all("ul",recursive=False)):
            for ul in li.findChildren("ul",recursive=False):
                getListItems(ul,tmp_list,cnt)
        else:
            tmp_list.append(toText(li))
    if cnt > 1:
        list.append(tmp_list)
    else:
        list.extend(tmp_list)
    return list

def splitEnhancements(listItems:list,enchancementKey:str) -> tuple:
    enhancements,augments,sets,mythic = [],[],[],[]
    for item in listItems[enchancementKey]:
        if "augment" in item.lower():
            augments.append(item)
        elif item in NAMED_ITEM_SETS:
            sets.append(item)
        elif "mythic" in item.lower() and "boost" in item.lower():
            mythic.append(item)
        else:
            enhancements.append(item)
    return (enhancements,augments,sets,mythic)

def getItemData(url:str) -> object:
    source = getSource(url)

    table = source.find("tbody")
    results = table.find_all("tr", recursive=False)
    item_data = {}

    for result in results:
        th = result.find("th")
        key = th.text.strip()
        
        td = result.find("td")
        if td.find("ul"):
            value = []
            for ul in td.findChildren("ul", recursive=False):
                enchantments,cnt = [],0
                value = getListItems(ul,enchantments,cnt)
        else:
            value = toText(td)
        item_data[key] = value
    if "Enhancements" in item_data.keys():
        enhancement_key = "Enhancements"
    elif "Enchantments" in item_data.keys():
        enhancement_key = "Enchantments"
    else:
        return "Can not find Enhancement Key."
    
    enhancements,augments,sets,mythic = splitEnhancements(item_data,enhancement_key)
    del item_data[enhancement_key]
    item_data["Enhancements"] = enhancements
    item_data["Augments"] = augments
    item_data["Named Item Sets"] = sets
    item_data["Mythic Bonus"] = mythic
    return item_data

def getNamedItemSets():
    NAMED_ITEM_SETS = []
    url = 'https://ddowiki.com/page/Named_item_sets'
    source = getSource(url)
    for wikitable in source.find_all('table',{"class":"wikitable"}):
        for tr in wikitable.tbody.find_all('tr'):
            for td in tr.find_all('td'):
                for span in td.find_all('span',id=True):
                    if span.next_sibling.name == 'b':
                        NAMED_ITEM_SETS.append(span.next_sibling.string.strip())
    return NAMED_ITEM_SETS

def insertItem(itemData):
    if cursor:
        insert_query = "INSERT INTO {table} ({columns})".format(
            table = "ddoloot_named_items",
            columns = "name,minimum_level,damage"
        )
        data_to_insert = ("Test Item", 29, "2d6+4")
        cursor.execute(insert_query,data_to_insert)
        connection.commit()
        print("Data inserted successfully!")

def getItemColumns():
    item_type_urls = {
        "armor": [
            "https://ddowiki.com/page/Item:Docent_of_Shadow_(level_32)",
            "https://ddowiki.com/page/Item:Legendary_Fancy_Flayer%27s_Date_Night_Duds",
            "https://ddowiki.com/page/Item:Legendary_Cavalry_Plate_(level_32)",
            "https://ddowiki.com/page/Item:Legendary_Privateer%27s_Leathers"
        ],
        "shield": [
            "https://ddowiki.com/page/Item:Legendary_Core_of_a_War_Machine",
            "https://ddowiki.com/page/Item:Legendary_Azure_Buckler",
            "https://ddowiki.com/page/Item:Legendary_Azure_Targe",
            "https://ddowiki.com/page/Item:Colossus,_the_Breaking_Wall",
            "https://ddowiki.com/page/Item:Legendary_Azure_Tower"
        ],
        "weapon": [
            "https://ddowiki.com/page/Item:Legendary_Shining_Reliquary_Greatsword",
            "https://ddowiki.com/page/Item:Legendary_Shining_Reliquary_Repeating_Heavy_Crossbow",
            "https://ddowiki.com/page/Item:Legendary_Shining_Reliquary_Handwraps",
            "https://ddowiki.com/page/Item:Flamesalt_Bastard_Sword"
        ],
        "jewelry/accessory": [
            "https://ddowiki.com/page/Item:Legendary_University_Sentry%27s_Helm",
            "https://ddowiki.com/page/Item:Legendary_Mystic_Monocle",
            "https://ddowiki.com/page/Item:Cloak_of_the_Zephyr",
            "https://ddowiki.com/page/Item:Bubble_Belt",
            "https://ddowiki.com/page/Item:Dustless_Boots",
            "https://ddowiki.com/page/Item:Legendary_Wristbound_Register",
            "https://ddowiki.com/page/Item:Ruby_Encrusted_Gauntlets",
            "https://ddowiki.com/page/Item:Torc_of_Prince_Raiyum-de_II",
            "https://ddowiki.com/page/Item:Ring_of_the_Archbishop",
            "https://ddowiki.com/page/Item:Ring_of_the_Silver_Concord",
            "https://ddowiki.com/page/Item:Legendary_Ring_of_the_Unlocked_Mind",
            "https://ddowiki.com/page/Item:Legendary_Library_Card"
        ]
    }

    master_item_list = {
        "armor":[],
        "shield":[],
        "weapon": [],
        "jewelry/accessory": []
    }

    for item_type in item_type_urls:
        for url in item_type_urls[item_type]:

            master_item_list[item_type].append(getItemData(url))

    master_key_list = {
        "armor":[],
        "shield":[],
        "weapon": [],
        "jewelry/accessory": []
    }

    for item_type in master_item_list:
        for item in master_item_list[item_type]:
            for key in item.keys():
                if key not in master_key_list[item_type]:
                    master_key_list[item_type].append(key)
    
    with open("results.json","w") as f:
        f.write(json.dumps(master_key_list,indent=2))
        


if __name__ == "__main__":

    # Import the environment variables containing our database credentials
    env_vars = dotenv_values(".env")

    #Get Named Item Sets
    NAMED_ITEM_SETS = getNamedItemSets()

    try:
        # Create database connection
        connection = mysql.connector.connect(
            host=env_vars["DATABASE_HOST"],
            database=env_vars["DATABASE_NAME"],
            port=env_vars["DATABASE_PORT"],
            user=env_vars["DATABASE_USERNAME"],
            password=env_vars["DATABASE_PASSWORD"]
        )

        # Verify that the sql connection is successful
        if connection.is_connected():
            cursor = connection.cursor()
            
    #         

    #         # Get Item Data
    #         url = "https://ddowiki.com/page/Item:The_Heart_of_the_Prince"
    #         item_data = getItemData(url)

    #         # Insert to database
    #         insertItem(item_data)

    #         # Get Data from Database
    #         # query = "SELECT * FROM wp_posts"
    #         # cursor.execute(query)

    #         # records = cursor.fetchall()

    #         # for row in records:
    #         #     print(row)

    except mysql.connector.Error as e:
        print("Error while connecting to MySQL database", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

    getItemColumns()
