from bs4 import BeautifulSoup
from dotenv import dotenv_values
import requests, sys, mysql.connector, logging, re, json
from mysql.connector import errorcode
import tools.column_mappings as column_mappings

LOG_FILE = "logs/run.log"

# Exit codes
UNKONWN = 3
CRITICAL = 2
WARNING = 1
OK = 0


def setup_logger():
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the root logger level to DEBUG

    # Create file handler and set level to debug
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)

    # Create console handler and set level to error
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter for file handler
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s [%(module)s : %(funcName)s] - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Create formatter for console handler
    console_formatter = logging.Formatter('%(levelname)s [%(module)s : %(funcName)s] %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# Create class to store our connection information in an object for easy querying
class createSQLConnection:
    def __init__(self,host:str,port:int,user:str,password:str,database:str) -> object:
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            if self.connection.is_connected():
                logging.info("Successfully connected to MySQL Database!")
                #return self.connection
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error(f"Something is wrong with your username and password. Full trace: {err}")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logging.error(f"Database does not exist. Full trace: {err}")
            else:
                logging.error(f"Unknown error occured. Full trace: {err}")
            sys.exit(CRITICAL)
    
    # Create method to send queries to our selected database
    def query(self,query:str,query_data:object=None):
        try:
            cursor = self.connection.cursor()
            try:
                logging.info("Succesfully created cursor!")
                cursor.execute(query,query_data)
                logging.info("Succesfully executed query!")
                results = cursor.fetchall()
                self.connection.commit()
                cursor.close()
                return results
            except Exception as e:
                logging.error(f"Failed to execute query --> query={query} || query_data={query_data} || Full trace: {e}")
                sys.exit(WARNING)
        except Exception as e:
            logging.error(f"Failed to create connector cursor. Full trace: {e}")

    # Create method to close our database connection
    def close(self):
        self.connection.close()


# Create a class to store our item object data
class ddo_item:
    table = "ddoloot_named_items"

    # Get source code from URL
    def __init__(self,url:str):
        self.url = url
        logging.info(f"Collecting HTML from {url}...")
        self.html = requests.get(self.url)
        if self.html.status_code == 200:
            logging.info(f"Succussfully collected HTML from {self.url}!")
            try:
                self.sourceCode = BeautifulSoup(self.html.content, 'html.parser')
                logging.info(f"Successfully parsed HTML from {self.url}!")
                self.get_item_data()
            except Exception as e:
                logging.error(f"Failed to parse HTML from {self.url}. Full trace: {e}")
    
    def verify_data(self) -> bool:
        # Define column names and types
        column_types = {
            'accepts_sentience': bool,
            'arcane_spell_failure': float,
            'armor_bonus': int,
            'armor_check_penalty': int,
            'armor_type': str,
            'attack_mod': str,
            'base_value': str,
            'binding': str,
            'critical_multiplier': int,
            'critical_threat_range': str,
            'critical_threat_percent': float,
            'damage': str,
            'damage_multiplier': float,
            'damage_dice': str,
            'damage_bonus': int,
            'damage_range_min': int,
            'damage_range_max': int,
            'damage_mod': str,
            'damage_reduction': str,
            'damage_type': str,
            'description': str,
            'durability': int,
            'enchantments': list,
            'augments': list,
            'feat_requirement': str,
            'handedness': str,
            'hardness': int,
            'item_name': str,
            'item_slot': str,
            'item_type': str,
            'location': list,
            'material': str,
            'maximum_dexterity_bonus': int,
            'minimum_level': int,
            'mythic_bonus': list,
            'named_item_sets': list,
            'notes': str,
            'proficiency_required': str,
            'race_absolutely_excluded': str,
            'race_absolutely_required': str,
            'required_trait': str,
            'shield_bonus': int,
            'shield_type': str,
            'tips': str,
            'upgradeable': str,
            'use_magic_device_dc': int,
            'weapon_type': str,
            'weight': float
        }
        logging.info(f"Verifying {self.data["item_name"]} for the correct column types.")
        for key,value in self.data.items():
            if key in column_types.keys():
                value_type = type(value).__name__
                column_type = column_types[key].__name__
                logging.debug(f"{self.item_name} -> key={key}, value={value}, value_type={type(self.data[key]).__name__}, expected_type={column_type}")
                if (value_type != column_type):
                    try:
                        match column_type:
                            case "str":
                                self.data[key] = str(value)
                            case "int":
                                if key == "use_magic_device_dc" and value == "No UMD needed": value = 0
                                self.data[key] = int(value)
                            case "float":
                                if key == "weight": value = value.replace(" lbs","")
                                self.data[key] = float(value)
                            case "bool":
                                if key == "arcane_spell_failure":
                                    if value > 1: value = value/100
                                if value.lower() in ["yes","true"]:
                                    self.data[key] = True
                                elif value.lower() in ["no","false"]:
                                    self.data[key] = False
                                else:
                                    logging.error(f"Could not mutate type of {self.data[key]} to boolean. Value={value}.")
                            case "list":
                                self.data[key] = [value]

                        if type(self.data[key]).__name__ != column_type:
                            logging.error(f"{self.item_name} still has the wrong data type for the {key} column. Should be {column_type}.")
                            logging.debug(f"{self.item_name} -> key={key}, value={value}, value_type={type(self.data[key]).__name__}, expected_type={column_type}")
                            return False
                        
                    except Exception as e:
                        logging.error(f"Unknown error occured. Full trace: {e}")
                        return False
            else:
                logging.error(f"{key} not found in column names, please update the 'verify_columns' method in the 'ddo_item' class.")
                return False

        # All columns were verified
        logging.info(f"{self.item_name} was successfully verfied!")
        return True


    # Remove any tooltip text so we don't have duplicate text in our database
    def remove_tooltip(self,object:object) -> object:
        try:
            if (object.find("span",{"class":"tooltip"})):
                for span in object.find_all("span",{"class":"tooltip"}): # Find all tooltip class spans
                    span.decompose() # Delete the tooltip span element
            return object
        except Exception as e:
            logging.error(f"Failed to remove tooltip. Full trace: {e}")
        
    # Clean up the feytwisted text
    def cleanse_feytwisted_text(self,object:object) -> object:
        try:
            if (object.find("a",{"title":"Feytwisted"})):
                object.find("br").insert_after("\n")
            return object
        except Exception as e:
            logging.error(f"Failed to cleanse Feytwisted text. Full trace: {e}")
    
    # Convert the tag contnet into a human readable string
    def to_text(self,object:object) -> str:
        try:
            self.remove_tooltip(object)
            self.cleanse_feytwisted_text(object)
            text = object.text.strip()
            text = text.replace("\u00a0"," ").replace("\u2014", "-")
            return text
        except Exception as e:
            logging.error(f"Failed to convert HTML tag contents to text. Full trace: {e}")
    
    # Recursively interate through list items to collect all text content in a clean format
    def get_list_items(self,object:object, list:list, cnt:int) -> object:
        try:
            tmp_list = []
            cnt += 1
            for li in object.find_all("li",recursive=False):
                if (li.find_all("ul",recursive=False)):
                    for ul in li.findChildren("ul",recursive=False):
                        self.get_list_items(ul,tmp_list,cnt)
                else:
                    tmp_list.append(self.to_text(li))
            if cnt > 1:
                list.append(tmp_list)
            else:
                list.extend(tmp_list)
            return list
        except Exception as e:
            logging.error(f"Failed to collect list items. Full trace: {e}")
    
    # Split the enchantments/enhancements section of the page into augments, named_item_sets, mythic_bonus, and finally enchantments
    def split_enchantments(self,listItems:list) -> tuple:
        try:
            enchanments,augments,sets,mythic = [],[],[],[]
            for item in listItems["enchantments"]:
                if "augment" in item.lower():
                    augments.append(item)
                elif item in NAMED_ITEM_SETS:
                    sets.append(item)
                elif "mythic" in item.lower() and "boost" in item.lower():
                    mythic.append(item)
                else:
                    enchanments.append(item)
            return (enchanments,augments,sets,mythic)
        except Exception as e:
            logging.error(f"Failed to split enchantments. Full trace: {e}")
    
    # Get the database column name to use as our key
    def convert_to_db_column(self,key:str) -> str:
        try:
            db_column = column_mappings.to_db_key(key)
            if (db_column == key):
                logging.error(f"Column mapping does not exist for key. Key=",key)
                sys.exit(CRITICAL)
            else:
                return db_column
        except Exception as e:
            logging.error(f"Failed to convert key string to database column. Key={key} - Full trace: {e}")

    # Main method responsible for iterating through the table rows of the item source code and parsing it into our item_data payload
    def get_item_data(self) -> object:
        self.data = {} # Initialize our item_data object
        try:
            source = self.sourceCode # Get our source code for the url
            self.data["item_name"] = source.find("span",{"class":"mw-headline"}).text # Get the item name
            self.item_name = self.data["item_name"]
            try:
                table = source.find("tbody") # Find the beginning of the data table
                try:
                    results = table.find_all("tr", recursive=False) # Find the first level of table rows ONLY
                    for result in results:
                        th = result.find("th") # Get the table row header
                        key = self.convert_to_db_column(th.text.strip()) # Get our DB column from the header
                        
                        td = result.find("td") # Get the table row data
                        if td.find("ul"): # Iterate through list if one exists
                            value = []
                            for ul in td.findChildren("ul", recursive=False):
                                enchantments,cnt = [],0
                                value = self.get_list_items(ul,enchantments,cnt)
                        else: # If no list item, then convert to string
                            value = self.to_text(td)

                        # Create additional damage attributes
                        if key == "damage_and_type":
                            pattern = r"^(?P<damage_multiplier>[^\[]*)\[(?P<damage_dice>\d\w\d+)[^\]]*\]\s*(?P<damage_bonus>[\+-]*\s*\d*)\s*(?P<damage_type>.*)"
                            dmg_regex = re.search(pattern,value)
                            if (dmg_regex):
                                self.data["damage"] = value
                                self.data["damage_multiplier"] = float(dmg_regex.group("damage_multiplier"))
                                self.data["damage_dice"] = dmg_regex.group("damage_dice")
                                self.data["damage_bonus"] = int(dmg_regex.group("damage_bonus").replace(" ",""))
                                self.data["damage_type"] = dmg_regex.group("damage_type")

                        # Seperate critical values
                        elif key == "critical_roll_and_multiplier":
                            pattern = r"^(?P<critical_threat_range>\d*-\d*)\s*/\s*x(?P<critical_multiplier>\d*)"
                            crit_regex = re.search(pattern,value)
                            if (crit_regex):
                                self.data["critical_threat_range"] = crit_regex.group("critical_threat_range")
                                self.data["critical_multiplier"] = crit_regex.group("critical_multiplier")
                        else:
                            self.data[key] = value # Update our item_data object
                    # Split the enchantments into the proper sections
                    enchantments,augments,sets,mythic = self.split_enchantments(self.data)
                    self.data["enchantments"] = enchantments
                    self.data["augments"] = augments
                    self.data["named_item_sets"] = sets
                    self.data["mythic_bonus"] = mythic

                    # Verify data
                    if (self.verify_data()):
                        # Return our item_data object
                        return self.data
                    else: 
                        logging.error(f"{self.item_name} data verification failed!")
                        sys.exit()
                except Exception as e:
                    logging.error(f"Failed to find 'tr' tag(s) in source code for {self.url}. Full trace: {e}")
            except Exception as e:
                logging.error(f"Failed to find 'tbody' tag in source code for {self.url}. Full trace: {e}")
        except Exception as e:
            logging.error(f"Failed to collect item data from {self.url}. Full trace: {e}")
    
    def insert_into_database(self,mysql_connection:object) -> bool:
        self.mysql_connection = mysql_connection # The connection object for our Database
        data_str = {} # Initialize a string version of the table if we need to insert a new row
        try:
            key_values = [] # Initialize the keys and values for our WHERE clause
            for key,value in self.data.items():
                key_values.append( f'{key}="{value}"')
                data_str[key] = str(value) # Add a string converted value into our data_str object
            where_clause = " AND ".join(key_values) # Create WHERE clause
            select_query = f"SELECT * FROM {self.table} WHERE {where_clause}"
            results = self.mysql_connection.query(select_query) # Does this item already exist?
            if (len(results) == 0): # Item does not exist, so create new row
                logging.info(f"{self.item_name} does not exist in the database. Creating new row...")
                columns = ', '.join(data_str.keys())
                placeholders = ', '.join(['%s' for _ in data_str.values()])
                values = tuple(data_str.values())
                insert_query = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
                try:
                    self.mysql_connection.query(insert_query,values)
                    logging.info(f"Successfully added {self.data["item_name"]}!")
                except Exception as e:
                    logging.error(f"Failed to insert item into database. Item Name: {self.item_name} - Full trace: {e}")
            else:
                logging.info(f"{self.item_name} already exists in the database.")
                logging.debug(f"{self.item_name} - select_query returned {len(results)} rows.")
        except:
            logging.error(f"Failed to insert {self.data["item_name"]} into database.")

# Collect a list of all Named Item sets (required for splitting our enchantments)
def get_named_item_sets() -> list:
    NAMED_ITEM_SETS = []
    url = 'https://ddowiki.com/page/Named_item_sets'

    logging.info(f"Collecting HTML from {url}...")
    html = requests.get(url)
    if html.status_code == 200:
        logging.info(f"Succussfully collected HTML from {url}!")
        try:
            source = BeautifulSoup(html.content, 'html.parser')
            logging.info(f"Successfully parsed HTML from {url}!")
            for wikitable in source.find_all('table',{"class":"wikitable"}):
                for tr in wikitable.tbody.find_all('tr'):
                    for td in tr.find_all('td'):
                        for span in td.find_all('span',id=True):
                            if span.next_sibling.name == 'b':
                                NAMED_ITEM_SETS.append(span.next_sibling.string.strip())
            return NAMED_ITEM_SETS
        except Exception as e:
            logging.error(f"Failed to parse HTML from {url}. Full trace: {e}")

if __name__ == "__main__":

    # Set up logging
    setup_logger()

    # Import the environment variables containing our database credentials
    env_vars = dotenv_values(".env")
    
    # Get Named Item Sets
    NAMED_ITEM_SETS = get_named_item_sets()

    # Configure our mySQL connection
    connection = createSQLConnection(
        host=env_vars["DATABASE_HOST"],
        port=env_vars["DATABASE_PORT"],
        user=env_vars["DATABASE_USERNAME"],
        password=env_vars["DATABASE_PASSWORD"],
        database=env_vars["DATABASE_NAME"]
    )

    COUNT = 0
    while (COUNT < 25):
        item = ddo_item("https://ddowiki.com/page/Item:Eidolon_of_the_Shadow")
        with open("item.json","w") as f:
            f.write(json.dumps(item.data,indent=2))
        item.insert_into_database(connection)