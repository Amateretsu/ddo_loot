from bs4 import BeautifulSoup
import requests
import re
import json
import os

exceptions = [
    'https://ddowiki.com/page/Item:Token_of_the_Twelve'
]

class Contains(str): # Changes == operator to be contains insead
    def __eq__(self, other):
        return self.__contains__(other)

def getSource(inputUrl):
    html = requests.get(inputUrl) # Request HTML from URL
    sourceCode = BeautifulSoup(html.content, 'html.parser') # Parse HTML
    return sourceCode
    

def getItemDetails(url,update=None):
    source = getSource(url)
    item = {}

    def next(source):
        return source.next_sibling

    item['update'] = update
    item['item_name'] = source.find('h2').find('span').next_sibling.text
    #print(item['item_name'])

    rows = source.tbody.findChildren('tr')
    for row in rows:
        for child in row.findChildren('th'):
            key = None
            #print(str(child.text).lower().replace('\n',''))
            match Contains(str(child.text).lower()):
                case "minimum level":
                    item['minimum_level'] = parse(row,'int')
                    print(item['minimum_level'])
                case "item type":
                    item['item_type'] = parse(row,'str')
                case "slot":
                    item['slot'] = parse(row,'str')
                case "armor type":
                    item['armor_type'] = parse(row,'str')
                    #item['armor_type'] = [str(child.string).strip() for child in row.findChildren('td')]
                case "shield type":
                    item['shield_type'] = parse(row,'str')
                    #item['shield_type'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "race absolutely required":
                    item['race_absolutely_required'] = parse(row,'str')
                    #item['race_absolutely_required'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "feat requirement":
                    item['feat_requirement'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "required trait":
                    item['required_trait'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "armor bonus":
                    item['armor_bonus'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "shield bonus":
                    item['shield_bonus'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "max dex bonus":
                    item['max_dex_bonus'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "damage reduction":
                    item['damage_reduction'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "armor check penalty":
                    item['armor_check_penalty'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "arcane spell failure":
                    item['arcane_spell_failure'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "damage":
                    item['damage'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "critical roll":
                    item['critical_roll'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "attack mod":
                    item['attack_mod'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "damage mod":
                    item['damage_mod'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "binding":
                    item['binding'] = [str(child.find('a').string).strip() for child in row.findChildren('td')][0].replace("\xa0"," ")
                case "durability":
                    durability = [child.string.strip() for child in row.findChildren('td')][0].replace("\n","")
                    if "/" in durability:
                        item['charges'] = str(durability)
                    else:
                        item['durability'] = int(durability)
                case "material":
                    item['material'] = [str(child.find('a').string).strip() for child in row.findChildren('td')][0]
                case "hardness":
                    item['hardness'] = int([str(child.string).strip() for child in row.findChildren('td')][0].replace("\n",""))
                case "base value":
                    for child in row.find_all('td'):
                        if child.string != None and re.search("<td>\n", str(child)) == None:
                            item['base_value'] = re.sub("<[^>]>","",str(child.string)).replace("\n","").strip()
                        #if child != None: item['base_value'] = int(str(child.find('span').string.strip()).replace('\n',''))
                case "weight":
                    item['weight'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "location":
                    item['location'] = [re.sub("<[^>]*>","",str(child)).replace("\n","").strip() for child in row.findChildren('td')]
                case "enchantments":
                    results = getEnchantments(row)
                    item['enchantments'] = results[0]
                    item['augment_slots'] = results[1]
                    item['item_sets'] = results[2]
                case "upgradeable?":
                    item['upgadeable'] = [str(child.string).strip() for child in row.findChildren('td')][0].replace("\n","")
                case "description":
                    item['description'] = [str(child.find('i').string).replace("\n","").strip() for child in row.findChildren('td')][0]
                case "notes":
                    item['notes'] = [re.sub("<[^>]*>","",str(child)).replace("\n","").strip() for child in row.findChildren('td')]
                case "tips":
                    item['tips'] = [str(child.find('p').string).replace("\n","").strip() for child in row.findChildren('td')][0]
    #print(item)
    #except: ""
    #json_export = json.dumps(item, indent=4)
    filepath = os.path.dirname(__file__)+r"\ItemJSONS"
    if update != None:
        if update < 10: update = "0"+str(update)
        filepath = filepath+r"\update_"+update
    os.makedirs(filepath, exist_ok=True)
    if item['item_name'] != "None":
        filename = item['item_name']
        # with open("{}\{}.json".format(filepath,filename), "w+") as file:
        #     json.dump(item,file,indent=4)

def parse(input_object,field_type):
    for child in input_object.find_all('td'):
        #print("INPUT :",child)
        if child.text != None:
            input_object = child.text.replace('\n','')
            print("OUTPUT:",input_object)

    match field_type:
        case "int":
            return int(input_object)
        case "str":
            return str(input_object)
        case "list":
            return [input_object]
            

def getEnchantments(row):
    item = {}
    enchantments = []
    augments = []
    sets = []

    for li in row.td.ul.findChildren('li'):
        value = li.span
        if value != None:
            for a in value.find('a'):
                if a.string in namedItemSets:
                    sets.append(a.string)
                elif "Augment Slot" in a.string:
                    augments.append(a.string)
                elif a.string not in enchantments:
                    enchantments.append(a.string.strip())
    return enchantments,augments,sets

def getNamedItemSets():
    url = 'https://ddowiki.com/page/Named_item_sets'
    source = getSource(url)
    namedItemSets= []
    count = 0
    for wikitable in source.find_all('table',{"class":"wikitable"}):
        for tr in wikitable.tbody.find_all('tr'):
            for td in tr.find_all('td'):
                for span in td.find_all('span',id=True):
                    if span.next_sibling.name == 'b':
                        namedItemSets.append(span.next_sibling.string.strip())
    return namedItemSets

def getItemUrls(url,update):
    href_url = "https://ddowiki.com/edit/Update_{}_named_items".format(update)
    source = getSource(url)
    url_list = []

    try:
        if source.find('a',href=href_url).string == 'Start this article':
            return "Page not created"
    except:
        for result in source.find_all('a',href=True):
            if "/Item:" in Contains(result):
                item_url = "https://ddowiki.com{}".format(re.findall("href=\"(\/[^\"]*)\"",str(result))[0])
                if item_url not in url_list:
                    url_list.append(item_url)
        return url_list
    
        
def getUpdateNamedItems():
    current = False
    urls = {}
    item_counts = {}
    update = 5

    while current == False:
        result = getItemUrls("https://ddowiki.com/page/Update_{}_named_items".format(update),update)
        if result != "Page not created":
            urls[update] = result
            item_counts[update] = len(result)
            current = True
            update += 1
        else:
            current = True
    return urls,item_counts

def bulkGetItemDetails():
    results = getUpdateNamedItems()
    urls = results[0]; item_counts = results[1]
    update = 5
    current = False
    all_updates = list(urls.keys())
    latest_update = all_updates[len(all_updates)-1]

    #while update <= latest_update:
    for item in urls[update]:
        print(item)
        getItemDetails(item,update)
        #update += 1




    
    

namedItemSets = getNamedItemSets()
getItemDetails('https://ddowiki.com/page/Item:The_Prince%27s_Gauntlet')
#getItemDetails('https://ddowiki.com/page/Item:Brimstone_Verge')

#bulkGetItemDetails()