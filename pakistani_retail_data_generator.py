"""
Pakistani Retail Data Generator for MS Fabric Project
Company: PakMart Traders (mirrors WideWorldImporters structure)
Author: Generated for MS Fabric Bronze Layer
Seed: 42 (fully deterministic)
"""

import csv
import random
import os
import math
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Seed for determinism ───────────────────────────────────────────────────────
random.seed(42)

# ── Output root ───────────────────────────────────────────────────────────────
BASE_DIR = Path("./pakmart_data")
FULL_DIR = BASE_DIR / "full"
INCR_DIR = BASE_DIR / "incremental"

DIRS = [
    FULL_DIR / "dimension_city",
    FULL_DIR / "dimension_customer",
    FULL_DIR / "dimension_date",
    FULL_DIR / "dimension_employee",
    FULL_DIR / "dimension_stock_item",
    FULL_DIR / "fact_sale",
    INCR_DIR / "fact_sale_1y_incremental",
]
for d in DIRS:
    d.mkdir(parents=True, exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
TS_FROM = "2013-01-01 00:00:00"
TS_TO   = "9999-12-31 23:59:59"

def ts(d: date) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")

def fmt_dec(v, places=2) -> str:
    return f"{v:.{places}f}"

def write_csv(path: Path, fieldnames: list, rows: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

# ══════════════════════════════════════════════════════════════════════════════
# REFERENCE DATA
# ══════════════════════════════════════════════════════════════════════════════

CITY_DATA = [
    # (CityName, StateProvince, SalesTerritory, Region, Subregion, lat_lon_approx, pop)
    ("Karachi",          "Sindh",                        "Karachi Region",     "South Asia", "Southern Pakistan", "24.8607° N, 67.0011° E", 14910352),
    ("Lahore",           "Punjab",                       "Lahore Region",      "South Asia", "Eastern Pakistan",  "31.5204° N, 74.3587° E", 11126285),
    ("Islamabad",        "Islamabad Capital Territory",  "Northern Region",    "South Asia", "Northern Pakistan", "33.6844° N, 73.0479° E", 1009832),
    ("Rawalpindi",       "Punjab",                       "Northern Region",    "South Asia", "Northern Pakistan", "33.6007° N, 73.0679° E", 2098231),
    ("Faisalabad",       "Punjab",                       "Central Punjab",     "South Asia", "Central Pakistan",  "31.4504° N, 73.1350° E", 3203846),
    ("Multan",           "Punjab",                       "Southern Punjab",    "South Asia", "Central Pakistan",  "30.1575° N, 71.5249° E", 1871843),
    ("Peshawar",         "Khyber Pakhtunkhwa",           "KPK Region",         "South Asia", "Northwestern Pakistan","34.0151° N, 71.5249° E", 1970042),
    ("Quetta",           "Balochistan",                  "Balochistan Region", "South Asia", "Western Pakistan",  "30.1798° N, 66.9750° E", 1001205),
    ("Hyderabad",        "Sindh",                        "Karachi Region",     "South Asia", "Southern Pakistan", "25.3960° N, 68.3578° E", 1732693),
    ("Sialkot",          "Punjab",                       "Lahore Region",      "South Asia", "Eastern Pakistan",  "32.4945° N, 74.5229° E", 655852),
    ("Gujranwala",       "Punjab",                       "Lahore Region",      "South Asia", "Eastern Pakistan",  "32.1877° N, 74.1945° E", 2027001),
    ("Abbottabad",       "Khyber Pakhtunkhwa",           "KPK Region",         "South Asia", "Northwestern Pakistan","34.1688° N, 73.2215° E", 148587),
    ("Bahawalpur",       "Punjab",                       "Southern Punjab",    "South Asia", "Central Pakistan",  "29.3956° N, 71.6722° E", 762111),
    ("Sargodha",         "Punjab",                       "Central Punjab",     "South Asia", "Central Pakistan",  "32.0836° N, 72.6711° E", 659862),
    ("Sukkur",           "Sindh",                        "Karachi Region",     "South Asia", "Southern Pakistan", "27.7052° N, 68.8574° E", 499900),
    ("Larkana",          "Sindh",                        "Karachi Region",     "South Asia", "Southern Pakistan", "27.5570° N, 68.2116° E", 490508),
    ("Mardan",           "Khyber Pakhtunkhwa",           "KPK Region",         "South Asia", "Northwestern Pakistan","34.2010° N, 72.0442° E", 358604),
    ("Mingora",          "Khyber Pakhtunkhwa",           "KPK Region",         "South Asia", "Northwestern Pakistan","34.7717° N, 72.3600° E", 279968),
    ("Dera Ghazi Khan",  "Punjab",                       "Southern Punjab",    "South Asia", "Central Pakistan",  "30.0489° N, 70.6340° E", 399064),
    ("Mirpur",           "Azad Kashmir",                 "AJK Region",         "South Asia", "Northern Pakistan", "33.1477° N, 73.7512° E", 456200),
    ("Gujrat",           "Punjab",                       "Lahore Region",      "South Asia", "Eastern Pakistan",  "32.5744° N, 74.0794° E", 390533),
    ("Sahiwal",          "Punjab",                       "Central Punjab",     "South Asia", "Central Pakistan",  "30.6682° N, 73.1066° E", 247706),
    ("Okara",            "Punjab",                       "Central Punjab",     "South Asia", "Central Pakistan",  "30.8138° N, 73.4534° E", 232386),
    ("Sheikhupura",      "Punjab",                       "Lahore Region",      "South Asia", "Eastern Pakistan",  "31.7167° N, 73.9850° E", 473129),
    ("Jhang",            "Punjab",                       "Central Punjab",     "South Asia", "Central Pakistan",  "31.2681° N, 72.3181° E", 414131),
    ("Rahim Yar Khan",   "Punjab",                       "Southern Punjab",    "South Asia", "Central Pakistan",  "28.4212° N, 70.2958° E", 420419),
    ("Kasur",            "Punjab",                       "Lahore Region",      "South Asia", "Eastern Pakistan",  "31.1167° N, 74.4500° E", 338494),
    ("Bannu",            "Khyber Pakhtunkhwa",           "KPK Region",         "South Asia", "Northwestern Pakistan","32.9886° N, 70.6058° E", 119069),
    ("Turbat",           "Balochistan",                  "Balochistan Region", "South Asia", "Western Pakistan",  "26.0025° N, 63.0430° E", 148000),
    ("Gilgit",           "Gilgit-Baltistan",             "Northern Region",    "South Asia", "Northern Pakistan", "35.9220° N, 74.3080° E", 216760),
]

MALE_NAMES = [
    "Muhammad Ali", "Ahmed Hassan", "Bilal Khan", "Usman Sheikh", "Asif Malik",
    "Imran Raza", "Tariq Hussain", "Zubair Ahmad", "Kamran Iqbal", "Faisal Chaudhry",
    "Shahzad Butt", "Naveed Anwar", "Junaid Mirza", "Salman Qureshi", "Adnan Farooqi",
    "Rizwan Siddiqui", "Hamza Baig", "Danish Niazi", "Waqas Bajwa", "Arif Noon",
    "Kashif Javed", "Nasir Mehmood", "Pervaiz Akhtar", "Shafiq Gill", "Tahir Lodhi",
]

FEMALE_NAMES = [
    "Ayesha Siddiqui", "Fatima Khan", "Zainab Ahmed", "Hira Malik", "Sara Hussain",
    "Nadia Raza", "Sana Iqbal", "Maham Sheikh", "Rabia Chaudhry", "Amina Baig",
    "Bushra Noor", "Saima Rehman", "Lubna Aslam", "Rukhsar Parveen", "Nusrat Jahan",
]

ALL_NAMES = MALE_NAMES + FEMALE_NAMES

BUSINESS_SUFFIXES = [
    "Traders", "Enterprises", "Brothers", "& Sons", "Distributors",
    "Wholesale", "General Store", "Mart", "Superstores", "Trading Co.",
    "Retail Hub", "Emporium", "Bazaar", "Market", "Stores",
]

CATEGORIES = ["Retailer", "Wholesaler", "Corporate", "Government", "Online Retailer"]

BUYING_GROUPS = [
    "PakMart Partners", "Independent", "Sindhi Traders",
    "Punjab Distributors", "KPK Merchants",
]

POSTAL_CODES = [
    "75500","54000","44000","46000","38000","60000","25000","87300",
    "71000","51310","52250","22010","63100","40100","65200","77150",
    "23200","19130","32200","13100","50700","57000","56300","39750",
    "35200","64200","55050","28100","92600","15100",
]

# ── Stock items ────────────────────────────────────────────────────────────────
# (Name, Color, SellingPkg, BuyingPkg, Brand, Size, LeadDays, QtyPerOuter,
#  IsChiller, TaxRate, UnitPrice, RRP, WeightKg, Category)
STOCK_ITEMS_RAW = [
    # Food / Grocery
    ("Basmati Rice 5kg Bag",        "N/A",   "Bag",    "Pallet",  "National Foods",  "5kg",    7,  20, False, 17.0,  1050.00, 1200.00, 5.100, "Food"),
    ("Desi Ghee 1L Tin",            "N/A",   "Tin",    "Carton",  "National Foods",  "1L",     5,  12, False, 17.0,  1950.00, 2200.00, 1.050, "Food"),
    ("Shan Masala Pack 100g",       "N/A",   "Pack",   "Carton",  "Shan Foods",      "100g",   3,  48, False, 17.0,    85.00,  120.00, 0.110, "Food"),
    ("Shan Biryani Mix 60g",        "N/A",   "Pack",   "Carton",  "Shan Foods",      "60g",    3,  48, False, 17.0,    55.00,   80.00, 0.065, "Food"),
    ("Rooh Afza Sherbet 800ml",     "Red",   "Bottle", "Carton",  "Rooh Afza",       "800ml",  5,  12, False, 17.0,   310.00,  350.00, 0.900, "Food"),
    ("Lipton Tea Bags 100pk",       "N/A",   "Pack",   "Carton",  "Lipton",          "100pk",  4,  24, False, 17.0,   480.00,  550.00, 0.220, "Food"),
    ("Tapal Danedar Tea 250g",      "N/A",   "Pack",   "Carton",  "National Foods",  "250g",   4,  24, False, 17.0,   190.00,  240.00, 0.260, "Food"),
    ("Dalda Cooking Oil 3L",        "N/A",   "Bottle", "Carton",  "National Foods",  "3L",     5,  12, False, 17.0,   720.00,  850.00, 2.800, "Food"),
    ("Sunflower Cooking Oil 5L",    "N/A",   "Bottle", "Carton",  "National Foods",  "5L",     5,   8, False, 17.0,  1150.00, 1300.00, 4.600, "Food"),
    ("Maida All-Purpose Flour 5kg", "White", "Bag",    "Pallet",  "National Foods",  "5kg",    7,  20, False, 17.0,   420.00,  500.00, 5.050, "Food"),
    ("Sugar 1kg Pack",              "White", "Pack",   "Pallet",  "PakMart Brand",   "1kg",    3,  50, False, 17.0,   120.00,  150.00, 1.010, "Food"),
    ("Iodized Salt 800g",           "White", "Pack",   "Carton",  "National Foods",  "800g",   3,  36, False, 17.0,    55.00,   75.00, 0.820, "Food"),
    ("Mixed Lentils Dal 1kg",       "Brown", "Pack",   "Pallet",  "National Foods",  "1kg",    5,  30, False, 17.0,   180.00,  220.00, 1.020, "Food"),
    # Clothing / Fabric
    ("Lawn Suit Unstitched 3pc",    "Multi", "Pack",   "Carton",  "Gul Ahmed",       "3pc",   10,  12, False, 17.0,  2200.00, 3000.00, 0.600, "Clothing"),
    ("Khaddar Fabric 3m",           "Brown", "Roll",   "Bale",    "Al-Karam",        "3m",    10,  10, False, 17.0,  1100.00, 1500.00, 0.800, "Clothing"),
    ("Denim Jeans Men",             "Blue",  "Each",   "Carton",  "Bonanza",         "32x32",  14, 10, False, 17.0,  2500.00, 3500.00, 0.750, "Clothing"),
    ("Shalwar Kameez Set Men",      "White", "Set",    "Carton",  "Junaid Jamshed",  "L",     12,   8, False, 17.0,  2800.00, 3800.00, 0.650, "Clothing"),
    ("Dupatta Chiffon 2.5m",        "Multi", "Each",   "Bundle",  "Gul Ahmed",       "2.5m",  10,  20, False, 17.0,   550.00,  800.00, 0.200, "Clothing"),
    ("Kurti Cotton Printed",        "Multi", "Each",   "Carton",  "Sapphire",        "M",     12,  12, False, 17.0,  1500.00, 2200.00, 0.350, "Clothing"),
    ("Lawn Kurta Men",              "White", "Each",   "Carton",  "ChenOne",         "L",     12,  10, False, 17.0,  1800.00, 2500.00, 0.400, "Clothing"),
    ("Kids School Uniform Set",     "White", "Set",    "Carton",  "PakMart Brand",   "10yr",  14,  12, False, 17.0,  1200.00, 1600.00, 0.550, "Clothing"),
    ("Wool Shawl Merino",           "Grey",  "Each",   "Bundle",  "Bonanza",         "One Size", 14, 10, False, 17.0, 2200.00, 3200.00, 0.450, "Clothing"),
    ("Chappals Leather Men",        "Tan",   "Pair",   "Carton",  "Servis",          "41",    10,  12, False, 17.0,  1400.00, 1900.00, 0.600, "Clothing"),
    ("Sneakers Canvas Women",       "White", "Pair",   "Carton",  "Bata",            "38",    12,  10, False, 17.0,  1900.00, 2500.00, 0.700, "Clothing"),
    ("Sandals Kids Rubber",         "Blue",  "Pair",   "Carton",  "Stylo",           "28",    10,  12, False, 17.0,   600.00,  900.00, 0.300, "Clothing"),
    # Electronics
    ("Mobile USB Charger 2A",       "White", "Each",   "Carton",  "PakMart Brand",   "2A",     7,  24, False, 17.0,   550.00,  800.00, 0.080, "Electronics"),
    ("Power Bank 10000mAh",         "Black", "Each",   "Carton",  "Orient",          "10000mAh", 10, 12, False, 17.0, 3200.00, 4500.00, 0.250, "Electronics"),
    ("LED Bulb 18W",                "White", "Each",   "Carton",  "EcoStar",         "18W",    7,  24, False, 17.0,   240.00,  320.00, 0.120, "Electronics"),
    ("Phone Case Universal 6inch",  "Black", "Each",   "Carton",  "PakMart Brand",   "6inch",  7,  24, False, 17.0,   250.00,  450.00, 0.050, "Electronics"),
    ("Electric Table Fan 12inch",   "White", "Each",   "Carton",  "Haier",           "12inch", 14,  6, False, 17.0,  4500.00, 6000.00, 2.100, "Electronics"),
    ("LED Strip Light 5m",          "White", "Roll",   "Carton",  "EcoStar",         "5m",    10,  12, False, 17.0,   850.00, 1200.00, 0.180, "Electronics"),
    ("Data Cable Type-C",           "Black", "Each",   "Carton",  "PakMart Brand",   "1m",     5,  48, False, 17.0,   180.00,  300.00, 0.040, "Electronics"),
    ("Extension Board 4Socket",     "White", "Each",   "Carton",  "EcoStar",         "1.8m",   7,  12, False, 17.0,   650.00,  950.00, 0.350, "Electronics"),
    ("Earphones Wired",             "Black", "Each",   "Carton",  "Orient",          "3.5mm",  7,  24, False, 17.0,   350.00,  550.00, 0.060, "Electronics"),
    # Household
    ("Plastic Storage Box Large",   "Blue",  "Each",   "Pallet",  "PakMart Brand",   "Large",  7,  12, False, 17.0,   450.00,  600.00, 1.200, "Household"),
    ("Steel Cooking Pot 5L",        "Silver","Each",   "Carton",  "PakMart Brand",   "5L",    10,   6, False, 17.0,  1600.00, 2200.00, 1.800, "Household"),
    ("Plastic Tumblers Set 6pc",    "Multi", "Set",    "Carton",  "PakMart Brand",   "350ml",  7,  12, False, 17.0,   300.00,  450.00, 0.600, "Household"),
    ("Cotton Bedsheet Double",      "White", "Each",   "Bale",    "ChenOne",         "Double", 10, 10, False, 17.0,  2000.00, 2800.00, 1.500, "Household"),
    ("Prayer Mat Velvet",           "Green", "Each",   "Bundle",  "PakMart Brand",   "Standard", 7, 12, False, 17.0, 700.00, 1000.00, 0.800, "Household"),
    ("Steel Pressure Cooker 7L",    "Silver","Each",   "Carton",  "PakMart Brand",   "7L",    10,   6, False, 17.0,  2800.00, 3800.00, 2.500, "Household"),
    ("Plastic Laundry Basket",      "Blue",  "Each",   "Pallet",  "PakMart Brand",   "Large",  7,  10, False, 17.0,   550.00,  750.00, 0.900, "Household"),
    ("Ceramic Dinner Set 12pc",     "White", "Set",    "Carton",  "PakMart Brand",   "12pc",  14,   4, False, 17.0,  2200.00, 3200.00, 4.000, "Household"),
    ("Iron Box Steam 2200W",        "Blue",  "Each",   "Carton",  "Haier",           "2200W", 14,   6, False, 17.0,  3200.00, 4500.00, 1.400, "Household"),
    ("Broom Plastic Handle",        "Green", "Each",   "Bundle",  "PakMart Brand",   "Standard", 5, 20, False, 17.0, 280.00,  400.00, 0.450, "Household"),
    ("Cleaning Mop Spin",           "Blue",  "Each",   "Carton",  "PakMart Brand",   "Standard", 7, 10, False, 17.0, 850.00, 1200.00, 1.100, "Household"),
    ("Bathroom Shower Curtain",     "White", "Each",   "Carton",  "PakMart Brand",   "180x180cm", 7, 12, False, 17.0, 600.00, 900.00, 0.700, "Household"),
    ("Pillow Fiber Fill Standard",  "White", "Each",   "Carton",  "ChenOne",         "Standard", 10, 12, False, 17.0, 450.00, 700.00, 0.600, "Household"),
    ("Comforter Winter Double",     "Multi", "Each",   "Carton",  "ChenOne",         "Double", 14,  6, False, 17.0, 3500.00, 5000.00, 2.200, "Household"),
    ("Dish Washing Liquid 500ml",   "Green", "Bottle", "Carton",  "National Foods",  "500ml",  3,  24, False, 17.0,  120.00,  180.00, 0.520, "Household"),
    ("Laundry Detergent Powder 3kg","Blue",  "Pack",   "Pallet",  "National Foods",  "3kg",    5,  12, False, 17.0,  480.00,  650.00, 3.050, "Household"),
    # Beverages (Chiller)
    ("Pepsi 1.5L Bottle",           "Black", "Bottle", "Carton",  "Pepsi",           "1.5L",   2,  12, True,  17.0,  100.00,  120.00, 1.530, "Beverage"),
    ("Coca-Cola 1.5L Bottle",       "Red",   "Bottle", "Carton",  "National Foods",  "1.5L",   2,  12, True,  17.0,  100.00,  120.00, 1.530, "Beverage"),
    ("Mineral Water 1.5L",          "Blue",  "Bottle", "Carton",  "Nestle",          "1.5L",   1,  12, True,  17.0,   70.00,   85.00, 1.510, "Beverage"),
    ("Mango Juice 1L Pack",         "Yellow","Pack",   "Carton",  "Nestle",          "1L",     2,  12, True,  17.0,  160.00,  200.00, 1.020, "Beverage"),
    ("Mineral Water 500ml",         "Blue",  "Bottle", "Carton",  "Nestle",          "500ml",  1,  24, True,  17.0,   35.00,   50.00, 0.510, "Beverage"),
    ("Apple Juice 1L Pack",         "Green", "Pack",   "Carton",  "Nestle",          "1L",     2,  12, True,  17.0,  170.00,  220.00, 1.020, "Beverage"),
    ("Lassi Sweet 500ml",           "White", "Bottle", "Carton",  "PakMart Brand",   "500ml",  1,  12, True,  17.0,   90.00,  120.00, 0.510, "Beverage"),
    ("Energy Drink 250ml Can",      "Blue",  "Can",    "Carton",  "Orient",          "250ml",  5,  24, False, 17.0,  130.00,  170.00, 0.270, "Beverage"),
]

# ══════════════════════════════════════════════════════════════════════════════
# 1. DIMENSION_CITY
# ══════════════════════════════════════════════════════════════════════════════

def generate_dimension_city():
    print("Generating dimension_city ...")
    fieldnames = [
        "CityKey","WWICityID","City","StateProvince","Country","Continent",
        "SalesTerritory","Region","Subregion","Location",
        "LatestRecordedPopulation","ValidFrom","ValidTo","LineageKey",
    ]
    rows = []
    for i, (city, state, terr, region, subreg, loc, pop) in enumerate(CITY_DATA, start=1):
        rows.append({
            "CityKey": i,
            "WWICityID": 10000 + i,
            "City": city,
            "StateProvince": state,
            "Country": "Pakistan",
            "Continent": "Asia",
            "SalesTerritory": terr,
            "Region": region,
            "Subregion": subreg,
            "Location": loc,
            "LatestRecordedPopulation": pop,
            "ValidFrom": TS_FROM,
            "ValidTo": TS_TO,
            "LineageKey": 1,
        })
    path = FULL_DIR / "dimension_city" / "dimension_city.csv"
    write_csv(path, fieldnames, rows)
    print(f"  → {len(rows)} rows written to {path}")
    return {r["CityKey"]: r for r in rows}


# ══════════════════════════════════════════════════════════════════════════════
# 2. DIMENSION_CUSTOMER
# ══════════════════════════════════════════════════════════════════════════════

def _make_business_name(rng):
    name = rng.choice(ALL_NAMES).split()[-1]          # use surname
    suffix = rng.choice(BUSINESS_SUFFIXES)
    return f"{name} {suffix}"

def generate_dimension_customer(n=500):
    print("Generating dimension_customer ...")
    rng = random.Random(42)
    fieldnames = [
        "CustomerKey","WWICustomerID","Customer","BillToCustomer",
        "Category","BuyingGroup","PrimaryContact","PostalCode",
        "ValidFrom","ValidTo","LineageKey",
    ]
    rows = []
    for i in range(1, n + 1):
        biz = _make_business_name(rng)
        # ~15 % of customers bill through a parent account
        bill_to = _make_business_name(rng) if rng.random() < 0.15 else biz
        rows.append({
            "CustomerKey": i,
            "WWICustomerID": 20000 + i,
            "Customer": biz,
            "BillToCustomer": bill_to,
            "Category": rng.choice(CATEGORIES),
            "BuyingGroup": rng.choice(BUYING_GROUPS),
            "PrimaryContact": rng.choice(ALL_NAMES),
            "PostalCode": rng.choice(POSTAL_CODES),
            "ValidFrom": TS_FROM,
            "ValidTo": TS_TO,
            "LineageKey": 1,
        })
    path = FULL_DIR / "dimension_customer" / "dimension_customer.csv"
    write_csv(path, fieldnames, rows)
    print(f"  → {len(rows)} rows written to {path}")
    return {r["CustomerKey"]: r for r in rows}


# ══════════════════════════════════════════════════════════════════════════════
# 3. DIMENSION_DATE
# ══════════════════════════════════════════════════════════════════════════════

MONTH_NAMES = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]
SHORT_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

def pak_fiscal(d: date):
    """Pakistani fiscal year runs July 1 – June 30."""
    if d.month >= 7:
        fy = d.year + 1          # FY2020 = July 2019 – June 2020
        fm = d.month - 6         # July → 1
    else:
        fy = d.year
        fm = d.month + 6         # January → 7
    return fy, fm

def generate_dimension_date(start_date=date(2019, 1, 1), end_date=date(2022, 12, 31)):
    print("Generating dimension_date ...")
    fieldnames = [
        "Date","DayNumber","Day","Month","ShortMonth",
        "CalendarMonthNumber","CalendarMonthLabel","CalendarYear","CalendarYearLabel",
        "FiscalMonthNumber","FiscalMonthLabel","FiscalYear","FiscalYearLabel",
        "ISOWeekNumber",
    ]
    rows = []
    current = start_date
    while current <= end_date:
        fy, fm = pak_fiscal(current)
        rows.append({
            "Date": current.strftime("%Y-%m-%d"),
            "DayNumber": current.day,
            "Day": current.strftime("%A"),
            "Month": MONTH_NAMES[current.month - 1],
            "ShortMonth": SHORT_MONTHS[current.month - 1],
            "CalendarMonthNumber": current.month,
            "CalendarMonthLabel": f"CY{current.year}-{SHORT_MONTHS[current.month-1]}",
            "CalendarYear": current.year,
            "CalendarYearLabel": f"CY{current.year}",
            "FiscalMonthNumber": fm,
            "FiscalMonthLabel": f"FY{fy}-{SHORT_MONTHS[current.month-1]}",
            "FiscalYear": fy,
            "FiscalYearLabel": f"FY{fy}",
            "ISOWeekNumber": current.isocalendar()[1],
        })
        current += timedelta(days=1)
    path = FULL_DIR / "dimension_date" / "dimension_date.csv"
    write_csv(path, fieldnames, rows)
    print(f"  → {len(rows)} rows written to {path}")
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# 4. DIMENSION_EMPLOYEE
# ══════════════════════════════════════════════════════════════════════════════

def generate_dimension_employee(n=25, n_salesperson=8):
    print("Generating dimension_employee ...")
    rng = random.Random(42)
    fieldnames = [
        "EmployeeKey","WWIEmployeeID","Employee","PreferredName",
        "IsSalesperson","Photo","ValidFrom","ValidTo","LineageKey",
    ]
    rows = []
    emp_names = rng.sample(ALL_NAMES, min(n, len(ALL_NAMES)))
    # pad if needed
    while len(emp_names) < n:
        emp_names.append(rng.choice(ALL_NAMES))

    salesperson_keys = set(range(1, n_salesperson + 1))

    for i, name in enumerate(emp_names[:n], start=1):
        preferred = name.split()[0]
        rows.append({
            "EmployeeKey": i,
            "WWIEmployeeID": 30000 + i,
            "Employee": name,
            "PreferredName": preferred,
            "IsSalesperson": i in salesperson_keys,
            "Photo": f"photos/emp_{i:03d}.jpg",
            "ValidFrom": TS_FROM,
            "ValidTo": TS_TO,
            "LineageKey": 1,
        })
    path = FULL_DIR / "dimension_employee" / "dimension_employee.csv"
    write_csv(path, fieldnames, rows)
    print(f"  → {len(rows)} rows written to {path}")
    salesperson_keys_list = list(salesperson_keys)
    return {r["EmployeeKey"]: r for r in rows}, salesperson_keys_list


# ══════════════════════════════════════════════════════════════════════════════
# 5. DIMENSION_STOCK_ITEM
# ══════════════════════════════════════════════════════════════════════════════

def generate_dimension_stock_item():
    print("Generating dimension_stock_item ...")
    fieldnames = [
        "StockItemKey","WWIStockItemID","StockItem","Color","SellingPackage",
        "BuyingPackage","Brand","Size","LeadTimeDays","QuantityPerOuter",
        "IsChillerStock","Barcode","TaxRate","UnitPrice","RecommendedRetailPrice",
        "TypicalWeightPerUnit","Photo","ValidFrom","ValidTo","LineageKey",
    ]
    rows = []
    rng = random.Random(42)
    for i, item in enumerate(STOCK_ITEMS_RAW, start=1):
        (name, color, sell_pkg, buy_pkg, brand, size, lead, qty_outer,
         is_chiller, tax, unit_price, rrp, weight, _cat) = item
        # Add slight price variance per item (±5 %)
        price_factor = rng.uniform(0.95, 1.05)
        up = round(unit_price * price_factor, 2)
        rrp_final = round(rrp * price_factor, 2)
        rows.append({
            "StockItemKey": i,
            "WWIStockItemID": 40000 + i,
            "StockItem": name,
            "Color": color,
            "SellingPackage": sell_pkg,
            "BuyingPackage": buy_pkg,
            "Brand": brand,
            "Size": size,
            "LeadTimeDays": lead,
            "QuantityPerOuter": qty_outer,
            "IsChillerStock": is_chiller,
            "Barcode": f"892{rng.randint(100000000,999999999)}",
            "TaxRate": fmt_dec(tax, 3),
            "UnitPrice": fmt_dec(up, 2),
            "RecommendedRetailPrice": fmt_dec(rrp_final, 2),
            "TypicalWeightPerUnit": fmt_dec(weight, 3),
            "Photo": f"photos/item_{i:03d}.jpg",
            "ValidFrom": TS_FROM,
            "ValidTo": TS_TO,
            "LineageKey": 1,
        })
    path = FULL_DIR / "dimension_stock_item" / "dimension_stock_item.csv"
    write_csv(path, fieldnames, rows)
    print(f"  → {len(rows)} rows written to {path}")
    return {r["StockItemKey"]: r for r in rows}


# ══════════════════════════════════════════════════════════════════════════════
# SALES SEASONALITY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

# Approximate Ramadan start dates (Gregorian) for 2019-2023
RAMADAN_STARTS = {
    2019: date(2019, 5, 5),
    2020: date(2020, 4, 24),
    2021: date(2021, 4, 13),
    2022: date(2022, 4, 2),
    2023: date(2023, 3, 23),
}

# Approximate Eid-ul-Fitr dates (day after Ramadan ~30 days)
EID_FITR = {yr: RAMADAN_STARTS[yr] + timedelta(days=30) for yr in RAMADAN_STARTS}

# Approximate Eid-ul-Adha dates
EID_ADHA = {
    2019: date(2019, 8, 11),
    2020: date(2020, 7, 31),
    2021: date(2021, 7, 20),
    2022: date(2022, 7, 9),
    2023: date(2023, 6, 28),
}

def sales_multiplier(d: date, category: str) -> float:
    """Return a daily demand multiplier (1.0 = baseline) based on Pakistani seasonality."""
    yr = d.year
    month = d.month

    mult = 1.0

    # Ramadan: groceries & food spike, clothing moderate spike
    ram_start = RAMADAN_STARTS.get(yr)
    if ram_start and timedelta(0) <= d - ram_start < timedelta(days=30):
        if category in ("Food", "Beverage"):
            mult *= random.uniform(1.6, 2.2)
        elif category == "Clothing":
            mult *= random.uniform(1.3, 1.8)
        else:
            mult *= random.uniform(0.8, 1.1)

    # Eid-ul-Fitr week: clothing & household
    eid_f = EID_FITR.get(yr)
    if eid_f and timedelta(0) <= d - eid_f < timedelta(days=7):
        if category == "Clothing":
            mult *= random.uniform(2.0, 3.0)
        elif category == "Household":
            mult *= random.uniform(1.5, 2.0)
        elif category in ("Food", "Beverage"):
            mult *= random.uniform(1.4, 1.9)

    # Eid-ul-Adha week: food & household
    eid_a = EID_ADHA.get(yr)
    if eid_a and timedelta(0) <= d - eid_a < timedelta(days=7):
        if category in ("Food", "Household"):
            mult *= random.uniform(1.8, 2.5)
        elif category == "Clothing":
            mult *= random.uniform(1.2, 1.6)

    # Summer (May-Aug): electronics (fans) spike, clothing light slump
    if month in (5, 6, 7, 8):
        if category == "Electronics":
            mult *= random.uniform(1.2, 1.6)
        elif category == "Clothing":
            mult *= random.uniform(0.75, 0.95)

    # Winter (Nov-Feb): clothing & household spike
    if month in (11, 12, 1, 2):
        if category in ("Clothing", "Household"):
            mult *= random.uniform(1.2, 1.5)

    # Weekend bump (Friday is big shopping day in Pakistan)
    if d.weekday() == 4:   # Friday
        mult *= random.uniform(1.1, 1.3)
    elif d.weekday() == 6: # Sunday
        mult *= random.uniform(0.85, 1.0)

    return max(0.2, mult)


# ══════════════════════════════════════════════════════════════════════════════
# 6. FACT_SALE  (2019-2022 full load, partitioned by year)
# 7. FACT_SALE_1Y_INCREMENTAL (2023)
# ══════════════════════════════════════════════════════════════════════════════

FACT_FIELDNAMES = [
    "SaleKey","CityKey","CustomerKey","BillToCustomerKey","StockItemKey",
    "InvoiceDateKey","DeliveryDateKey","SalespersonKey","WWIInvoiceID",
    "Description","Package","Quantity","UnitPrice","TaxRate",
    "TotalExcludingTax","TaxAmount","Profit","TotalIncludingTax",
    "TotalDryItems","TotalChillerItems","LineageKey",
]

def _build_fact_rows(
    rng,
    city_keys, customer_map, stock_map, salesperson_keys,
    start_date: date, end_date: date,
    target_rows: int,
    sale_key_start: int = 1,
):
    """Build a list of fact_sale dicts for the given date range."""

    # Pre-compute category per stock item for seasonality
    item_category = {}
    for i, item in enumerate(STOCK_ITEMS_RAW, start=1):
        item_category[i] = item[13]  # last element is category

    # Create date list
    all_dates = []
    cur = start_date
    while cur <= end_date:
        all_dates.append(cur)
        cur += timedelta(days=1)

    total_days = len(all_dates)
    rows = []
    sale_key = sale_key_start
    wii_invoice = 900000 + sale_key_start

    # Distribute rows across dates using seasonality weights
    # First pass: compute weight per date (summed across a sample of items)
    sample_items = list(stock_map.keys())[:10]
    date_weights = []
    for d in all_dates:
        w = sum(sales_multiplier(d, item_category.get(sk, "Food")) for sk in sample_items)
        date_weights.append(w)

    total_weight = sum(date_weights)
    # Assign approximate number of transactions per date
    rows_per_date = [max(1, int(round(target_rows * w / total_weight))) for w in date_weights]
    # Adjust to hit target
    diff = target_rows - sum(rows_per_date)
    for i in range(abs(diff)):
        idx = i % total_days
        rows_per_date[idx] += 1 if diff > 0 else -1
        rows_per_date[idx] = max(1, rows_per_date[idx])

    stock_keys = list(stock_map.keys())
    customer_keys = list(customer_map.keys())

    for d_idx, d in enumerate(all_dates):
        n_tx = rows_per_date[d_idx]
        for _ in range(n_tx):
            city_key = rng.choice(city_keys)
            cust_key = rng.choice(customer_keys)
            cust = customer_map[cust_key]
            bill_to_name = cust["BillToCustomer"]
            # Find a customer key matching bill_to or use same
            bill_to_key = cust_key  # simplified – use same key for bill-to
            stock_key = rng.choice(stock_keys)
            item = stock_map[stock_key]
            sp_key = rng.choice(salesperson_keys)

            unit_price = float(item["UnitPrice"])
            tax_rate = float(item["TaxRate"])
            is_chiller = item["IsChillerStock"]

            # Quantity: chiller items sell more single units
            if is_chiller:
                qty = rng.randint(1, 48)
            elif item["SellingPackage"] in ("Bag", "Bale", "Pallet"):
                qty = rng.randint(1, 10)
            else:
                qty = rng.randint(1, 20)

            total_excl = round(unit_price * qty, 2)
            tax_amount = round(total_excl * tax_rate / 100, 6)
            total_incl = round(total_excl + tax_amount, 6)
            # Cost ~60-80% of unit price
            cost_pct = rng.uniform(0.60, 0.80)
            profit = round(total_excl - round(unit_price * cost_pct * qty, 2), 2)

            delivery_date = d + timedelta(days=rng.randint(1, int(item["LeadTimeDays"])))

            rows.append({
                "SaleKey": sale_key,
                "CityKey": city_key,
                "CustomerKey": cust_key,
                "BillToCustomerKey": bill_to_key,
                "StockItemKey": stock_key,
                "InvoiceDateKey": ts(d),
                "DeliveryDateKey": ts(delivery_date),
                "SalespersonKey": sp_key,
                "WWIInvoiceID": wii_invoice,
                "Description": item["StockItem"],
                "Package": item["SellingPackage"],
                "Quantity": qty,
                "UnitPrice": fmt_dec(unit_price, 2),
                "TaxRate": item["TaxRate"],
                "TotalExcludingTax": fmt_dec(total_excl, 2),
                "TaxAmount": fmt_dec(tax_amount, 6),
                "Profit": fmt_dec(profit, 2),
                "TotalIncludingTax": fmt_dec(total_incl, 6),
                "TotalDryItems": 0 if is_chiller else qty,
                "TotalChillerItems": qty if is_chiller else 0,
                "LineageKey": 1,
            })
            sale_key += 1
            wii_invoice += 1

    return rows, sale_key


def generate_fact_sale(city_keys, customer_map, stock_map, salesperson_keys,
                       target_rows=200000):
    print("Generating fact_sale (2019-2022, partitioned by year) ...")
    rng = random.Random(42)
    years = [2019, 2020, 2021, 2022]
    rows_per_year = target_rows // len(years)
    total_written = 0
    sale_key_counter = 1

    for yr in years:
        start = date(yr, 1, 1)
        end   = date(yr, 12, 31)
        print(f"  Building year {yr} (~{rows_per_year} rows) ...", end=" ", flush=True)
        year_rows, sale_key_counter = _build_fact_rows(
            rng, city_keys, customer_map, stock_map, salesperson_keys,
            start, end, rows_per_year, sale_key_counter,
        )
        path = FULL_DIR / "fact_sale" / f"fact_sale_{yr}.csv"
        write_csv(path, FACT_FIELDNAMES, year_rows)
        print(f"{len(year_rows)} rows → {path}")
        total_written += len(year_rows)

    print(f"  → Total fact_sale rows: {total_written}")
    return total_written, sale_key_counter


def generate_fact_sale_incremental(city_keys, customer_map, stock_map, salesperson_keys,
                                   sale_key_start: int, target_rows=60000):
    print("Generating fact_sale_1y_incremental (2023) ...")
    rng = random.Random(99)   # different seed for incremental
    start = date(2023, 1, 1)
    end   = date(2023, 12, 31)
    rows, _ = _build_fact_rows(
        rng, city_keys, customer_map, stock_map, salesperson_keys,
        start, end, target_rows, sale_key_start,
    )
    path = INCR_DIR / "fact_sale_1y_incremental" / "fact_sale_2023.csv"
    write_csv(path, FACT_FIELDNAMES, rows)
    print(f"  → {len(rows)} rows written to {path}")
    return len(rows)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  PakMart Traders – Data Generator")
    print("  MS Fabric Bronze Layer (Pakistani Retail)")
    print("=" * 60)
    print()

    city_map      = generate_dimension_city()
    customer_map  = generate_dimension_customer(n=500)
    _date_rows    = generate_dimension_date()
    employee_map, salesperson_keys = generate_dimension_employee(n=25, n_salesperson=8)
    stock_map     = generate_dimension_stock_item()

    city_keys = list(city_map.keys())

    fact_total, next_sale_key = generate_fact_sale(
        city_keys, customer_map, stock_map, salesperson_keys,
        target_rows=200000,
    )

    incr_total = generate_fact_sale_incremental(
        city_keys, customer_map, stock_map, salesperson_keys,
        sale_key_start=next_sale_key,
        target_rows=60000,
    )

    print()
    print("=" * 60)
    print("  SUMMARY – Row Counts")
    print("=" * 60)
    print(f"  dimension_city              : {len(city_map):>10,}")
    print(f"  dimension_customer          : {len(customer_map):>10,}")
    print(f"  dimension_date              : {len(_date_rows):>10,}")
    print(f"  dimension_employee          : {len(employee_map):>10,}")
    print(f"  dimension_stock_item        : {len(stock_map):>10,}")
    print(f"  fact_sale (2019-2022)       : {fact_total:>10,}")
    print(f"  fact_sale_1y_incremental    : {incr_total:>10,}")
    print(f"  {'GRAND TOTAL':<28}: {len(city_map)+len(customer_map)+len(_date_rows)+len(employee_map)+len(stock_map)+fact_total+incr_total:>10,}")
    print()
    print(f"  Output directory: {BASE_DIR.resolve()}")
    print("=" * 60)
    print("  Done!")


if __name__ == "__main__":
    main()
