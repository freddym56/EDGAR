#!/xbrldata/.venv/bin/python3.12
# -*- coding: utf-8 -*-
"""
:mod:`EdgarRenderer.viewer`
~~~~~~~~~~~~~~~~~~~
Edgar(tm) Renderer was created by staff of the U.S. Securities and Exchange Commission.
Data and content created by government employees within the scope of their employment
are not subject to domestic copyright protection. 17 U.S.C. 105.

This is the sec.gov module cgi-bin/viewer and also the EDGAR plugin module render/viewer.py
for transformation of the FilingSummary.xml element tree into html for SEC Workstation and
Arelle operation in desktop and other integrations.

It generates what is known as the "mustard menu" (even though it's now blue), to select
EdgarRender output "R" files or the inline xbrl viewer.

When operated as a cgi-bin module the query parameters that are utilized are the accession_number,
and cik.  These allow the cgi-bin to access the FilingSummary.xml file on the sec.gov website
S3 file system and to access filer information on that environment for the header and footers
of the hosted webpage.

When operated as a transformation method for Arelle plugin EDGAR the FilingSummary is passed in
as an etree of Elements, and an accession number (if available) is used as appropriate, but the
public website footers and filer information are not available and not shown.

In both cases the resulting html is returned as a string (in standard out for cgi-bin, and as
a returned string for the transformation method invocation.

Installation as a cgi-bin module:
   1 - Ensure NO DOS CRLF line endings, if checked out from GitLab use dos2unix.
   2 - Please remove the .py suffix from the module, and provide read and chmod a+rx for permissions.
   3 - You may also have to adjust the first line specifying the executable to the venv or system
       copy of Python which has the below imported modules installed.

Installation for web development and testing: please note the env parameter VIEWER_ENV_MODE which may
be set to
   0 (no cgi-bin web use debugging),
   1 (cgi-bin web development),
   2 (web development and testing)
   3 (cgi-bin with MySQL database access).
Or if you wish set the default under the IS_DEV_MODE line below to 0, 1, 2 or 3.
Also note the stub, log and data paths for development testing in cgi-mode.
Mode 0 must be used when running under EDGAR plugin as a transformation replacement for xslt.

Installation for EDGAR plugin to Arelle development:  the env parameter is not applicable, please
use a Python IDE for debugging.  IS_DEV_MODE is reset to 0 in this mode.

EDGAR plugin parameters for use of viewer.py as a transformation method:  specify "viewer.py"
as the value for cmd line or GUI parameter for applicable transformation (instead of the xslt file
name), e.g.:
   --summaryXslt viewer.py

"""

# normally available python library modules
import os
import sys
import traceback
from datetime import datetime
from collections import OrderedDict
import json
# library modules which may need "pip" installation and updating for cgi-bin usage
import cgi
import cgitb
import requests
import regex as re
import urllib.parse
from lxml import etree, html

# --- Environment Configuration ---
IS_DEV_ENV = int(os.environ.get('VIEWER_ENV_MODE', '3'))  # 0=prod or Arelle, 1=web dev, 2=web dev+debug, 3=database + debug

if IS_DEV_ENV == 0:
    FILING_DATA_PATH = 'https://s3.amazonaws.com/' + transform_s3_bucket(bucket_name) + '/edgar/data'
else:
    MYSQL_STUB_FILE = "/xbrldata/team_sun_stars/test/viewer/MySql_stub.json"
    DEBUG_LOG_FILE = "/xbrldata/team_sun_stars/test/viewer/viewerLog.txt"
    FILING_DATA_PATH = 'http://md-ud-edgxbrl01:8082/Archives/edgar/data'

# --- Constants ---
VERSION = 2.25
FILER_CODE = {
    "f": "Filer",
    "b": "Filed by",
    "p": "Filed for",
    "s": "Serial",
    "c": "Subject",
    "r": "Reporting",
    "i": "Issuer"
}

# note: these are the codes used by the predecessor Perl implementation
# PyPi module naicskit also contains SIC codes but seems to have different numbering
sic_codes = {
    '0100': "Agricultural Production-Crops",
    '0200': "Agricultural Prod-Livestock & Animal Specialties",
    '0700': "Agricultural Services",
    '0800': "Forestry",
    '0900': "Fishing, Hunting and Trapping",
    '1000': "Metal Mining",
    '1040': "Gold and Silver Ores",
    '1044': "Silver Ores",
    '1090': "Miscellaneous Metal Ores",
    '1220': "Silver Ores",
    '1221': "Bituminous Coal & Lignite Surface Mining",
    '1311': "Crude Petroleum & Natural Gas",
    '1381': "Drilling Oil & Gas Wells",
    '1382': "Oil & Gas Field Exploration Services",
    '1389': "Oil & Gas Field Services, NEC",
    '1400': "Mining & Quarrying of  Nonmetallic Minerals (No Fuels)",
    '1520': "General Bldg Contractors - Residential Bldgs",
    '1531': "Operative Builders",
    '1540': "General Bldg Contractors - Nonresidential Bldgs",
    '1600': "Heavy Construction Other Than Bldg Const - Contractors",
    '1623': "Water, Sewer, Pipeline, Comm & Power Line Construction",
    '1700': "Construction - Special Trade Contractors",
    '1731': "Electrical Work",
    '2000': "Food and Kindred Products",
    '2011': "Meat Packing Plants",
    '2013': "Sausages & Other Prepared Meat Products",
    '2015': "Poultry Slaughtering and Processing",
    '2020': "Dairy Products",
    '2024': "Ice Cream & Frozen Desserts",
    '2030': "Canned, Frozen & Preservd Fruit, Veg & Food Specialties",
    '2033': "Canned, Fruits, Veg, Preserves, Jams & Jellies",
    '2040': "Grain Mill Products",
    '2050': "Bakery Products",
    '2052': "Cookies & Crackers",
    '2060': "Sugar & Confectionery Products",
    '2070': "Fats & Oils",
    '2080': "Beverages",
    '2082': "Malt Beverages",
    '2086': "Bottled & Canned Soft Drinks & Carbonated Waters",
    '2090': "Miscellaneous Food Preparations & Kindred Products",
    '2092': "Prepared Fresh or  Frozen Fish & Seafoods",
    '2100': "Tobacco Products",
    '2111': "Cigarettes",
    '2200': "Textile Mill Products",
    '2211': "Broadwoven Fabric Mills, Cotton",
    '2221': "Broadwoven Fabric Mills, Man Made Fiber & Silk",
    '2250': "Knitting Mills",
    '2253': "Knit Outerwear Mills",
    '2273': "Carpets & Rugs",
    '2300': "Apparel & Other Finishd Prods of  Fabrics & Similar Matl",
    '2320': "Men's & Boys' Furnishgs, Work Clothg, & Allied Garments",
    '2330': "Women's, Misses', and Juniors Outerwear",
    '2340': "Women's, Misses', Children's & Infants' Undergarments",
    '2390': "Miscellaneous Fabricated Textile Products",
    '2400': "Lumber & Wood Products (No Furniture)",
    '2421': "Sawmills & Planting Mills, General",
    '2430': "Millwood, Veneer, Plywood, & Structural Wood Members",
    '2451': "Mobile Homes",
    '2452': "Prefabricated Wood Bldgs & Components",
    '2510': "Household Furniture",
    '2511': "Wood Household Furniture, (No Upholstered)",
    '2520': "Office Furniture",
    '2522': "Office Furniture (No Wood)",
    '2531': "Public Bldg & Related Furniture",
    '2540': "Partitions, Shelvg, Lockers, & of fice & Store Fixtures",
    '2590': "Miscellaneous Furniture & Fixtures",
    '2600': "Papers & Allied Products",
    '2611': "Pulp Mills",
    '2621': "Paper Mills",
    '2631': "Paperboard Mills",
    '2650': "Paperboard Containers & Boxes",
    '2670': "Converted Paper & Paperboard Prods (No Contaners/Boxes)",
    '2673': "Plastics, Foil & Coated Paper Bags",
    '2711': "Newspapers: Publishing or  Publishing & Printing",
    '2721': "Periodicals: Publishing or  Publishing & Printing",
    '2731': "Books: Publishing or  Publishing & Printing",
    '2732': "Book Printing",
    '2741': "Miscellaneous Publishing",
    '2750': "Commercial Printing",
    '2761': "Manifold Business Forms",
    '2771': "Greeting Cards",
    '2780': "Blankbooks, Looseleaf Binders & Bookbindg & Relatd Work",
    '2790': "Service Industries For The Printing Trade",
    '2800': "Chemicals & Allied Products",
    '2810': "Industrial Inorganic Chemicals",
    '2820': "Plastic Material, Synth Resin/Rubber, Cellulos (No Glass)",
    '2821': "Plastic Materials, Synth Resins & Nonvulcan Elastomers",
    '2833': "Medicinal Chemicals & Botanical Products",
    '2834': "Pharmaceutical Preparations",
    '2835': "In Vitro & In Vivo Diagnostic Substances",
    '2836': "Biological Products, (No Diagnostic Substances)",
    '2840': "Soap, Detergents, Cleang Preparations, Perfumes, Cosmetics",
    '2842': "Specialty Cleaning, Polishing and Sanitation Preparations",
    '2844': "Perfumes, Cosmetics & Other Toilet Preparations",
    '2851': "Paints, Varnishes, Lacquers, Enamels & Allied Prods",
    '2860': "Industrial Organic Chemicals",
    '2870': "Agricultural Chemicals",
    '2890': "Miscellaneous Chemical Products",
    '2891': "Adhesives & Sealants",
    '2911': "Petroleum Refining",
    '2950': "Asphalt Paving & Roofing Materials",
    '2990': "Miscellaneous Products of  Petroleum & Coal",
    '3011': "Tires & Inner Tubes",
    '3021': "Rubber & Plastics Footwear",
    '3050': "Gaskets, Packg & Sealg Devices & Rubber & Plastics Hose",
    '3060': "Fabricated Rubber Products, NEC",
    '3080': "Miscellaneous Plastics Products",
    '3081': "Unsupported Plastics Film & Sheet",
    '3086': "Plastics Foam Products",
    '3089': "Plastics Products, NEC",
    '3100': "Leather & Leather Products",
    '3140': "Footwear, (No Rubber)",
    '3211': "Flat Glass",
    '3220': "Glass & Glassware, Pressed or  Blown",
    '3221': "Glass Containers",
    '3231': "Glass Products, Made of  Purchased Glass",
    '3241': "Cement, Hydraulic",
    '3250': "Structural Clay Products",
    '3260': "Pottery & Related Products",
    '3270': "Concrete, Gypsum & Plaster Products",
    '3272': "Concrete Products, Except Block & Brick",
    '3281': "Cut Stone & Stone Products",
    '3290': "Abrasive, Asbestos & Misc Nonmetallic Mineral Prods",
    '3310': "Steel Works, Blast Furnaces & Rolling & Finishing Mills",
    '3312': "Steel Works, Blast Furnaces & Rolling Mills (Coke Ovens)",
    '3317': "Steel Pipe & Tubes",
    '3320': "Iron & Steel Foundries",
    '3330': "Primary Smelting & Refining of  Nonferrous Metals",
    '3334': "Primary Production of  Aluminum",
    '3341': "Secondary Smelting & Refining of  Nonferrous Metals",
    '3350': "Rolling Drawing & Extruding of  Nonferrous Metals",
    '3357': "Drawing & Insulating of  Nonferrous Wire",
    '3360': "Nonferrous Foundries (Castings)",
    '3390': "Miscellaneous Primary Metal Products",
    '3411': "Metal Cans",
    '3412': "Metal Shipping Barrels, Drums, Kegs & Pails",
    '3420': "Cutlery, Handtools & General Hardware",
    '3430': "Heating Equip, Except Elec & Warm Air; & Plumbing Fixtures",
    '3433': "Heating Equipment, Except Electric & Warm Air Furnaces",
    '3440': "Fabricated Structural Metal Products",
    '3442': "Metal Doors, Sash, Frames, Moldings & Trim",
    '3443': "Fabricated Plate Work (Boiler Shops)",
    '3444': "Sheet Metal Work",
    '3448': "Prefabricated Metal Buildings & Components",
    '3451': "Screw Machine Products",
    '3452': "Bolts, Nuts, Screws, Rivets & Washers",
    '3460': "Metal Forgings & Stampings",
    '3470': "Coating, Engraving & Allied Services",
    '3480': "Ordnance & Accessories, (No Vehicles/Guided Missiles)",
    '3490': "Miscellaneous Fabricated Metal Products",
    '3510': "Engines & Turbines",
    '3523': "Farm Machinery & Equipment",
    '3524': "Lawn & Garden Tractors & Home Lawn & Gardens Equip",
    '3530': "Construction, Mining & Materials Handling Machinery & Equip",
    '3531': "Construction Machinery & Equip",
    '3532': "Mining Machinery & Equip (No Oil & Gas Field Mach & Equip)",
    '3533': "Oil & Gas Field Machinery & Equipment",
    '3537': "Industrial Trucks, Tractors, Trailors & Stackers",
    '3540': "Metalworkg Machinery & Equipment",
    '3541': "Machine Tools, Metal Cutting Types",
    '3550': "Special Industry Machinery (No Metalworking Machinery)",
    '3555': "Printing Trades Machinery & Equipment",
    '3559': "Special Industry Machinery, NEC",
    '3560': "General Industrial Machinery & Equipment",
    '3561': "Pumps & Pumping Equipment",
    '3562': "Ball & Roller Bearings",
    '3564': "Industrial & Commercial Fans & Blowers & Air Purifing Equip",
    '3567': "Industrial Process Furnaces & Ovens",
    '3569': "General Industrial Machinery & Equipment, NEC",
    '3570': "Computer & office Equipment",
    '3571': "Electronic Computers",
    '3572': "Computer Storage Devices",
    '3575': "Computer Terminals",
    '3576': "Computer Communications Equipment",
    '3577': "Computer Peripheral Equipment, NEC",
    '3578': "Calculating & Accounting Machines (No Electronic Computers)",
    '3579': "Office Machines, NEC",
    '3580': "Refrigeration & Service Industry Machinery",
    '3585': "Air-Cond & Warm Air Heatg Equip & Comm & Indl Refrig Equip",
    '3590': "Misc Industrial & Commercial Machinery & Equipment",
    '3600': "Electronic & Other Electrical Equipment (No Computer Equip)",
    '3612': "Power, Distribution & Specialty Transformers",
    '3613': "Switchgear & Switchboard Apparatus",
    '3620': "Electrical Industrial Apparatus",
    '3621': "Motors & Generators",
    '3630': "Household Appliances",
    '3634': "Electric Housewares & Fans",
    '3640': "Electric Lighting & Wiring Equipment",
    '3651': "Household Audio & Video Equipment",
    '3652': "Phonograph Records & Prerecorded Audio Tapes & Disks",
    '3661': "Telephone & Telegraph Apparatus",
    '3663': "Radio & Tv Broadcasting & Communications Equipment",
    '3669': "Communications Equipment, NEC",
    '3670': "Electronic Components & Accessories",
    '3672': "Printed Circuit Boards",
    '3674': "Semiconductors & Related Devices",
    '3677': "Electronic Coils, Transformers & Other Inductors",
    '3678': "Electronic Connectors",
    '3679': "Electronic Components, NEC",
    '3690': "Miscellaneous Electrical Machinery, Equipment & Supplies",
    '3695': "Magnetic & Optical Recording Media",
    '3711': "Motor Vehicles & Passenger Car Bodies",
    '3713': "Truck & Bus Bodies",
    '3714': "Motor Vehicle Parts & Accessories",
    '3715': "Truck Trailers",
    '3716': "Motor Homes",
    '3720': "Aircraft & Parts",
    '3721': "Aircraft",
    '3724': "Aircraft Engines & Engine Parts",
    '3728': "Aircraft Parts & Auxiliary Equipment, NEC",
    '3730': "Ship & Boat Building & Repairing",
    '3743': "Railroad Equipment",
    '3751': "Motorcycles, Bicycles & Parts",
    '3760': "Guided Missiles & Space Vehicles & Parts",
    '3790': "Miscellaneous Transportation Equipment",
    '3812': "Search, Detection, Navigation, Guidance, Aeronautical Sys",
    '3821': "Laboratory Apparatus & Furniture",
    '3822': "Auto Controls For Regulating Residential & Comml Environments",
    '3823': "Industrial Instruments For Measurement, Display, and Control",
    '3824': "Totalizing Fluid Meters & Counting Devices",
    '3825': "Instruments For Meas & Testing of  Electricity & Elec Signals",
    '3826': "Laboratory Analytical Instruments",
    '3827': "Optical Instruments & Lenses",
    '3829': "Measuring & Controlling Devices, NEC",
    '3841': "Surgical & Medical Instruments & Apparatus",
    '3842': "Orthopedic, Prosthetic & Surgical Appliances & Supplies",
    '3843': "Dental Equipment & Supplies",
    '3844': "X-Ray Apparatus & Tubes & Related Irradiation Apparatus",
    '3845': "Electromedical & Electrotherapeutic Apparatus",
    '3851': "Ophthalmic Goods",
    '3861': "Photographic Equipment & Supplies",
    '3873': "Watches, Clocks, Clockwork Operated Devices/Parts",
    '3910': "Jewelry, Silverware & Plated Ware",
    '3911': "Jewelry, Precious Metal",
    '3931': "Musical Instruments",
    '3942': "Dolls & Stuffed Toys",
    '3944': "Games, Toys & Children's Vehicles (No Dolls & Bicycles)",
    '3949': "Sporting & Athletic Goods, NEC",
    '3950': "Pens, Pencils & Other Artists' Materials",
    '3960': "Costume Jewelry & Novelties",
    '3990': "Miscellaneous Manufacturing Industries",
    '4011': "Railroads, Line-Haul Operating",
    '4013': "Railroad Switching & Terminal Establishments",
    '4100': "Local & Suburban Transit & Interurban Hwy Passenger Trans",
    '4210': "Trucking & Courier Services (No Air)",
    '4213': "Trucking (No Local)",
    '4220': "Public Warehousing & Storage",
    '4231': "Terminal Maintenance Facilities For Motor Freight Transport",
    '4400': "Water Transportation",
    '4412': "Deep Sea Foreign Transportation of  Freight",
    '4512': "Air Transportation, Scheduled",
    '4513': "Air Courier Services",
    '4522': "Air Transportation, Nonscheduled",
    '4581': "Airports, Flying Fields & Airport Terminal Services",
    '4610': "Pipe Lines (No Natural Gas)",
    '4700': "Transportation Services",
    '4731': "Arrangement of  Transportation of  Freight & Cargo",
    '4812': "Radiotelephone Communications",
    '4813': "Telephone Communications (No Radiotelephone)",
    '4822': "Telegraph & Other Message Communications",
    '4832': "Radio Broadcasting Stations",
    '4833': "Television Broadcasting Stations",
    '4841': "Cable & Other Pay Television Services",
    '4899': "Communications Services, NEC",
    '4900': "Electric, Gas & Sanitary Services",
    '4911': "Electric Services",
    '4922': "Natural Gas Transmission",
    '4923': "Natural Gas Transmisison & Distribution",
    '4924': "Natural Gas Distribution",
    '4931': "Electric & Other Services Combined",
    '4932': "Gas & Other Services Combined",
    '4941': "Water Supply",
    '4950': "Sanitary Services",
    '4953': "Refuse Systems",
    '4955': "Hazardous Waste Management",
    '4961': "Steam & Air-Conditioning Supply",
    '4991': "Cogeneration Services & Small Power Producers",
    '5000': "Wholesale-Durable Goods",
    '5010': "Wholesale-Motor Vehicles & Motor Vehicle Parts & Supplies",
    '5013': "Wholesale-Motor Vehicle Supplies & New Parts",
    '5020': "Wholesale-Furniture & Home Furnishings",
    '5030': "Wholesale-Lumber & Other Construction Materials",
    '5031': "Wholesale-Lumber, Plywood, Millwork & Wood Panels",
    '5040': "Wholesale-Professional & Commercial Equipment & Supplies",
    '5045': "Wholesale-Computers & Peripheral Equipment & Software",
    '5047': "Wholesale-Medical, Dental & Hospital Equipment & Supplies",
    '5050': "Wholesale-Metals & Minerals (No Petroleum)",
    '5051': "Wholesale-Metals Service Centers & of fices",
    '5063': "Wholesale-Electrical Apparatus & Equipment, Wiring Supplies ",
    '5064': "Wholesale-Electrical Appliances, Tv & Radio Sets",
    '5065': "Wholesale-Electronic Parts & Equipment, NEC",
    '5070': "Wholesale-Hardware & Plumbing & Heating Equipment & Supplies",
    '5072': "Wholesale-Hardware",
    '5080': "Wholesale-Machinery, Equipment & Supplies",
    '5082': "Wholesale-Construction & Mining (No Petro) Machinery & Equip",
    '5084': "Wholesale-Industrial Machinery & Equipment",
    '5090': "Wholesale-Misc Durable Goods",
    '5094': "Wholesale-Jewelry, Watches, Precious Stones & Metals",
    '5099': "Wholesale-Durable Goods, NEC",
    '5110': "Wholesale-Paper & Paper Products",
    '5122': "Wholesale-Drugs, Proprietaries & Druggists' Sundries",
    '5130': "Wholesale-Apparel, Piece Goods & Notions",
    '5140': "Wholesale-Groceries & Related Products",
    '5141': "Wholesale-Groceries, General Line",
    '5150': "Wholesale-Farm Product Raw Materials",
    '5160': "Wholesale-Chemicals & Allied Products",
    '5171': "Wholesale-Petroleum Bulk Stations & Terminals",
    '5172': "Wholesale-Petroleum & Petroleum Products (No Bulk Stations)",
    '5180': "Wholesale-Beer, Wine & Distilled Alcoholic Beverages",
    '5190': "Wholesale-Miscellaneous Nondurable Goods",
    '5200': "Retail-Building Materials, Hardware, Garden Supply",
    '5211': "Retail-Lumber & Other Building Materials Dealers",
    '5271': "Retail-Mobile Home Dealers",
    '5311': "Retail-Department Stores",
    '5331': "Retail-Variety Stores",
    '5399': "Retail-Misc General Merchandise Stores",
    '5400': "Retail-Food Stores",
    '5411': "Retail-Grocery Stores",
    '5412': "Retail-Convenience Stores",
    '5500': "Retail-Auto Dealers & Gasoline Stations",
    '5531': "Retail-Auto & Home Supply Stores",
    '5600': "Retail-Apparel & Accessory Stores",
    '5621': "Retail-Women's Clothing Stores",
    '5651': "Retail-Family Clothing Stores",
    '5661': "Retail-Shoe Stores",
    '5700': "Retail-Home Furniture, Furnishings & Equipment Stores",
    '5712': "Retail-Furniture Stores",
    '5731': "Retail-Radio, Tv & Consumer Electronics Stores",
    '5734': "Retail-Computer & Computer Software Stores",
    '5735': "Retail-Record & Prerecorded Tape Stores",
    '5810': "Retail-Eating & Drinking Places",
    '5812': "Retail-Eating  Places",
    '5900': "Retail-Miscellaneous Retail",
    '5912': "Retail-Drug Stores and Proprietary Stores",
    '5940': "Retail-Miscellaneous Shopping Goods Stores",
    '5944': "Retail-Jewelry Stores",
    '5945': "Retail-Hobby, Toy & Game Shops",
    '5960': "Retail-Nonstore Retailers",
    '5961': "Retail-Catalog & Mail-Order Houses",
    '5990': "Retail-Retail Stores, NEC",
    '6021': "National Commercial Banks",
    '6022': "State Commercial Banks",
    '6029': "Commercial Banks, NEC",
    '6035': "Savings Institution, Federally Chartered",
    '6036': "Savings Institutions, Not Federally Chartered",
    '6099': "Functions Related To Depository Banking, NEC",
    '6111': "Federal & Federally-Sponsored Credit Agencies",
    '6141': "Personal Credit Institutions",
    '6153': "Short-Term Business Credit Institutions",
    '6159': "Miscellaneous Business Credit Institution",
    '6162': "Mortgage Bankers & Loan Correspondents",
    '6163': "Loan Brokers",
    '6172': "Finance Lessors",
    '6189': "Asset-Backed Securities",
    '6199': "Finance Services",
    '6200': "Security & Commodity Brokers, Dealers, Exchanges & Services",
    '6211': "Security Brokers, Dealers & Flotation Companies",
    '6221': "Commodity Contracts Brokers & Dealers",
    '6282': "Investment Advice",
    '6311': "Life Insurance",
    '6321': "Accident & Health Insurance",
    '6324': "Hospital & Medical Service Plans",
    '6331': "Fire, Marine & Casualty Insurance",
    '6351': "Surety Insurance",
    '6361': "Title Insurance",
    '6399': "Insurance Carriers, NEC",
    '6411': "Insurance Agents, Brokers & Service",
    '6500': "Real Estate",
    '6510': "Real Estate Operators (No Developers) & Lessors",
    '6512': "Opeators of  Nonresidential Buildings",
    '6513': "Operators of  Apartment Buildings",
    '6519': "Lessors of  Real Property, NEC",
    '6531': "Real Estate Agents & Managers (For Others)",
    '6532': "Real Estate Dealers (For Their Own Account)",
    '6552': "Land Subdividers & Developers (No Cemeteries)",
    '6770': "Blank Checks",
    '6792': "Oil Royalty Traders",
    '6794': "Patent Owners & Lessors",
    '6795': "Mineral Royalty Traders",
    '6798': "Real Estate Investment Trusts",
    '6799': "Investors, NEC",
    '7000': "Hotels, Rooming Houses, Camps & Other Lodging Places",
    '7011': "Hotels & Motels",
    '7200': "Services-Personal Services",
    '7310': "Services-Advertising",
    '7311': "Services-Advertising Agencies",
    '7320': "Services-Consumer Credit Reporting, Collection Agencies",
    '7330': "Services-Mailing, Reproduction, Commercial Art & Photography",
    '7331': "Services-Direct Mail Advertising Services",
    '7340': "Services-To Dwellings & Other Buildings",
    '7350': "Services-Miscellaneous Equipment Rental & Leasing",
    '7359': "Services-Equipment Rental & Leasing, NEC",
    '7361': "Services-Employment Agencies",
    '7363': "Services-Help Supply Services",
    '7370': "Services-Computer Programming, Data Processing, Etc.",
    '7371': "Services-Computer Programming Services",
    '7372': "Services-Prepackaged Software",
    '7373': "Services-Computer Integrated Systems Design",
    '7374': "Services-Computer Processing & Data Preparation",
    '7377': "Services-Computer Rental & Leasing",
    '7380': "Services-Miscellaneous Business Services",
    '7381': "Services-Detective, Guard & Armored Car Services",
    '7384': "Services-Photofinishing Laboratories",
    '7385': "Services-Telephone Interconnect Systems",
    '7389': "Services-Business Services, NEC",
    '7500': "Services-Automotive Repair, Services & Parking",
    '7510': "Services-Auto Rental & Leasing (No Drivers)",
    '7600': "Services-Miscellaneous Repair Services",
    '7812': "Services-Motion Picture & Video Tape Production",
    '7819': "Services-Allied To Motion Picture Production",
    '7822': "Services-Motion Picture & Video Tape Distribution",
    '7829': "Services-Allied To Motion Picture Distribution",
    '7830': "Services-Motion Picture Theaters",
    '7841': "Services-Video Tape Rental",
    '7900': "Services-Amusement & Recreation Services",
    '7948': "Services-Racing, Including Track Operation",
    '7990': "Services-Miscellaneous Amusement & Recreation",
    '7997': "Services-Membership Sports & Recreation Clubs",
    '8000': "Services-Health Services",
    '8011': "Services-Offices & Clinics of  Doctors of  Medicine",
    '8050': "Services-Nursing & Personal Care Facilities",
    '8051': "Services-Skilled Nursing Care Facilities",
    '8060': "Services-Hospitals",
    '8062': "Services-General Medical & Surgical Hospitals, NEC",
    '8071': "Services-Medical Laboratories",
    '8082': "Services-Home Health Care Services",
    '8090': "Services-Misc Health & Allied Services, NEC",
    '8093': "Services-Specialty Outpatient Facilities, NEC",
    '8111': "Services-Legal Services",
    '8200': "Services-Educational Services",
    '8300': "Services-Social Services",
    '8351': "Services-Child Day Care Services",
    '8600': "Services-Membership or ganizations",
    '8700': "Services-Engineering, Accounting, Research, Management",
    '8711': "Services-Engineering Services",
    '8731': "Services-Commercial Physical & Biological Research",
    '8734': "Services-Testing Laboratories",
    '8741': "Services-Management Services",
    '8742': "Services-Management Consulting Services",
    '8744': "Services-Facilities Support Management Services",
    '8880': "American Depositary Receipts",
    '8888': "Foreign Governments",
    '8900': "Services-Services, NEC",
    '9721': "International Affairs",
    '9995': "Non-Operating Establishments"
}

alias_path = "" # holds full path to filing directory in S3 bucket

# --- Debug Logging ---
def log_debug(message):
    if IS_DEV_ENV in (2, 3):
        with open(DEBUG_LOG_FILE, "a") as logf:
            logf.write(f"{message}\n")

# --- Error Handling ---
def build_error_html(errors):
    if not errors:
        return ''
    error_div = html.Element('div', style="margin-top: 15px; margin: 15px 20px 10px 20px; color: red; text-align: center;")
    for msg in errors:
        p = html.Element('p')
        p.text = msg
        error_div.append(p)
    return etree.tostring(error_div, pretty_print=True, method='html', encoding='unicode')

# --- Stub Data and DB Access ---
def get_filer_data(accession_number_dashed, db_connection=None):
    errors = []
    if IS_DEV_ENV in (1, 2):
        try:
            with open(MYSQL_STUB_FILE) as f:
                stub_data = json.load(f)
            log_debug(f"Accession number: {accession_number_dashed}")
            if not accession_number:
                errors.append("Missing accession number parameter.")
                log_debug("Accession number parameter missing")
            result = stub_data.get(accession_number_dashed)
            if result is None:
                result = stub_data.get("default", {})
                log_debug("Using default stub entry")
            log_debug(f"Filer info from json file: {json.dumps(result)}")
            return result, errors # note that result is a list of dicts
        except Exception as e:
            errors.append(f"Error loading stub data from json file: {e}")
            log_debug(f"Error loading stub data from json file: {e}")
            return [], errors
    else: # IS_DEV_ENV in (0, 3)
        # Production DB logic here
        try:
            cursor = db_connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT accession_number, filer_sequence, filer_type, filed_by_form_type,
                       conformed_name, cik, assigned_sic, irs_number, state_of_incorporation,
                       fiscal_year_end, street1, street2, city, state, zip, phone,
                       m_street1, m_street2, m_city, m_state, m_zip, owner_org
                FROM filer WHERE accession_number = %s
            """, (accession_number_dashed,))
            result = cursor.fetchall()
            for r in result:
                # log_debug(f"r = {r}")
                cursor.execute("""
                    SELECT form_type, act, file_number, film_number
                    FROM filing_values WHERE accession_number = %s AND cik = %s and filer_type = %s and filer_sequence = %s
                """, (r["accession_number"], r["cik"], r["filer_type"], r["filer_sequence"]))
                r["filing_info"] = cursor.fetchall()
            cursor.close()
            if IS_DEV_ENV == 3:
                log_debug(f"Filer info from database: {json.dumps(result)}")
            return result, errors
        except Exception as e:
            errors.append(f"Error loading filer data from database: {e}")
            if IS_DEV_ENV == 3:
                log_debug(f"Error loading filer data from database: {e}, exception traceback: {traceback.format_exception(*sys.exc_info())}")
            return [], errors

# --- XML Parsing ---
def parse_reports(xml_path_or_etree): # xml_path can be string (in CGI mode) or etree (transformation mode)
    instancesReports = OrderedDict()
    filingSummaryParsed = fs = {
        "instancesReports": instancesReports, # key is instance orig file name, list is report objects
        "base_taxonomies": (),
        "doc1": ""
        } # filing_summary results
    try:
        if isinstance(xml_path_or_etree, str):
            # CGI mode, fetch FilingSummary file
            log_debug(f"FilingSummary path: {xml_path_or_etree}")
            response = requests.get(xml_path_or_etree)
            xml_bytes = response.content
            log_debug(f"FilingSummary xml type: {type(xml_bytes)} bytes: {xml_bytes}")
            filing_summary = etree.fromstring(xml_bytes)
        else:
            # transformation mode, already an etree of Elements
            assert isinstance(xml_path_or_etree, etree._Element), "Must be an etree FilingSummary"
            filing_summary = xml_path_or_etree

        my_reports = filing_summary.find('MyReports')
        reports = []
        if my_reports is not None:
            for report in my_reports.findall('Report'):
                instance = report.get("instance")
                if instance:
                    if instance not in instancesReports:
                        instancesReports[instance] = {"reports":[]}
                    instancesReports[instance]["reports"].append(report)
                    reports.append(report)
        base_taxonomies_elem = filing_summary.find('BaseTaxonomies')
        base_taxonomies = base_taxonomies_elem.findall('BaseTaxonomy') if base_taxonomies_elem is not None else []
        fs["base_taxonomies"] = base_taxonomies

        # Map InputFiles by instance/original ---
        input_files_elem = filing_summary.find('InputFiles')
        input_files = []
        if input_files_elem is not None:
            input_files = input_files_elem.findall('File')
        # Build a mapping: instance/original -> InputFile element
        input_file_map = {}
        for f in input_files:
            original = f.get('original')
            if original and original in instancesReports:
                input_file_map[original] = f
                ir = instancesReports[original]
                ir["doc1"] = original
                ir["isRr"] = f.get('isRR') == "true"
                ir["isoef"] = f.get('isOEF') == "true"
                ir["isn2prospectus"] = f.get('isN2Prospectus') == "true"
                ir["isn3n4n6"] = f.get('isVip') == "true"
                ir["isfeeexhibit"] = f.get('isFeeExhibit') == "true"
                ir["isNcsr"] = f.get('isNcsr') == "true"
                ir["isProxy"] = f.get('isProxy') == "true"
                ir["isN1a"] = f.get('isN1a') == "true"
                ir["isSdr"] = f.get('isSdr') == "true"
                ir["isOnlyShr"] = f.get('isOnlyShr') == "true"
                ir["isRxp"] = f.get('isRxp') == "true"
                ir["isUsgaap"] = f.get('isUsgaap') == "true"
                ir["isIfrs"] = f.get('isIfrs') == "true"
                ir["isOnlyDei"] = f.get('isOnlyDei') == "true"
                ir["isDefinitelyFs"] = f.get('isDefinitelyFs') == "true"
                ir["isDefinitelyNotFs"] = (
                    ir["isOnlyShr"] or ir["isRxp"] or ir["isN1a"] or ir["isn3n4n6"]  or ir["isn2prospectus"]  or ir["isfeeexhibit"] or ir["isProxy"] or ir["isSdr"] or ir["isOnlyDei"]
                                  or (ir["isNcsr"] and not(ir["isDefinitelyFs"])))
                ir["mayHaveExcel"] = ir["isOnlyDei"] or ir["isDefinitelyFs"]
                log_debug(f"Instance {original} flags: {', '.join(p+'='+str(v) for (p,v) in ir.items() if p.startswith('is'))}")

        # For each report, copy matching InputFile attributes onto report
        for report in reports:
            instance = report.get('instance')
            if instance and instance in input_file_map:
                f = input_file_map[instance]
                for k, v in f.attrib.items():
                    report.attrib[k] = v
                report.attrib['isinline'] = str(os.path.splitext(instance)[1].lower() in (".htm", ".xhtml")).lower()
        # categorization hints
        fs["majorversion"] = filing_summary.findtext('Version','.').partition('.')[0]
        fs["nreports"] = len(reports)
        fs["nbooks"] = sum(1 for r in reports if r.find('ReportType','') == 'Book')
    except Exception as e:
        log_debug(f"Error parsing XML: {e}, Traceback: {traceback.format_tb(sys.exc_info()[2])}")
    return filingSummaryParsed

# --- HTML Output ---
def build_banner():
    banner_div = html.Element('div', {'id': 'header', 'style': 'text-align: center;'})
    nav = html.Element('nav', {'id': 'main-navbar', 'class': 'navbar navbar-expand'})
    ul_nav = html.Element('ul', {'class': 'navbar-nav'})
    # SEC logo
    li_logo = html.Element('li', {'class': 'nav-item'})
    a_logo = html.Element('a', {'class': 'nav__sec_link', 'href': 'https://www.sec.gov'})
    img_logo = html.Element('img', src='/edgar/search/images/edgar-logo-2x.png', alt='', style='height:6.25rem')
    a_logo.append(img_logo)
    li_logo.append(a_logo)
    ul_nav.append(li_logo)
    # SEC.gov link
    li_sec = html.Element('li', {'class': 'nav-item'})
    a_sec = html.Element('a', {'class': 'nav__sec_link', 'href': 'https://www.sec.gov'})
    span_sec = html.Element('span', {'class': 'link-text d-inline'})
    span_sec.text = 'SEC.gov'
    a_sec.append(span_sec)
    li_sec.append(a_sec)
    ul_nav.append(li_sec)
    # EDGAR link
    li_edgar = html.Element('li', {'class': 'nav-item'})
    a_edgar = html.Element('a', {'class': 'nav__link', 'href': 'https://www.sec.gov/submit-filings/about-edgar', 'id': 'edgar-short-form'})
    span_edgar = html.Element('span', {'class': 'link-text'})
    span_edgar.text = 'EDGAR'
    a_edgar.append(span_edgar)
    li_edgar.append(a_edgar)
    ul_nav.append(li_edgar)
    nav.append(ul_nav)
    # Right-side nav
    ul_nav_right = html.Element('ul', {'class': 'navbar-nav ml-auto'})
    li_faq = html.Element('li', {'class': 'nav-item'})
    a_faq = html.Element('a', {'href': 'https://www.sec.gov/edgar/search/efts-faq.html', 'class': 'nav__link', 'target': '_blank', 'rel': 'noopener noreferrer'})
    a_faq.text = 'FAQ'
    li_faq.append(a_faq)
    ul_nav_right.append(li_faq)
    li_search = html.Element('li', {'class': 'nav-item'})
    a_search = html.Element('a', {'href': 'https://www.sec.gov/edgar/search-and-access', 'class': 'nav__link'})
    a_search.text = 'Filings search tools'
    li_search.append(a_search)
    ul_nav_right.append(li_search)
    nav.append(ul_nav_right)
    banner_div.append(nav)
    # Heading
    h1 = html.Element('h1', style='position: relative; top: -40px;')
    h1.text = 'View Filing Data'
    banner_div.append(h1)
    return banner_div

def build_breadcrumbs(cik='', accession_number='', accession_number_dashed='', filename=''):
    breadcrumbs_div = html.Element('div', {'id': 'breadCrumbs'})
    ul = html.Element('ul')
    # SEC Home
    li_home = html.Element('li')
    a_home = html.Element('a', href='/')
    a_home.text = 'SEC Home'
    li_home.append(a_home)
    li_home.tail = ' »'
    ul.append(li_home)
    # Company Search
    li_search = html.Element('li')
    a_search = html.Element('a', href='/edgar/searchedgar/companysearch.html')
    a_search.text = 'Company Search'
    li_search.append(a_search)
    li_search.tail = ' »'
    ul.append(li_search)
    # Filing Information (if filename is present)
    if filename:
        li_filing = html.Element('li')
        filing_url = f'/Archives/edgar/data/{cik}/{accession_number}/{accession_number_dashed}-index.htm'
        a_filing = html.Element('a', href=filing_url)
        a_filing.text = 'Filing Information'
        li_filing.append(a_filing)
        li_filing.tail = ' »'
        ul.append(li_filing)
    # Current Page
    li_current = html.Element('li', {'class': 'last'})
    li_current.text = 'Current Page'
    ul.append(li_current)
    breadcrumbs_div.append(ul)
    hr = html.Element('hr')
    breadcrumbs_div.append(hr)
    return breadcrumbs_div

def build_company_header(cik, filer_data):
    from lxml import html

    if not filer_data:
        return html.Element('div')  # Empty if no data

    filer = filer_data[0] if isinstance(filer_data, list) else filer_data

    header_div = html.Element('div', {
        'class': 'companyHeader',
        'style': 'margin-bottom: 10px; font-size: 1.2em; font-weight: bold;'
    })

    # Company Name and CIK (with EDGAR filings link)
    company_name = filer.get('conformed_name', '')
    span_company = html.Element('span', {'class': 'companyName'})
    span_company.text = company_name

    # CIK link to EDGAR filings
    if cik:
        span_company.text += f" (CIK: "
        cik_link = html.Element('a', {
            'href': f'/cgi-bin/browse-edgar?CIK={cik}&action=getcompany',
            'target': '_blank',
            'style': 'text-decoration: underline; color: #0074d9;'
        })
        cik_link.text = cik
        span_company.append(cik_link)
        span_company.text += ")"

    header_div.append(span_company)
    return header_div

def build_html(mode, cik, accession_number, accession_number_dashed, alias_path, filer_data, filingSummaryParsed, errors):
    # mode = server for CGI environment, transform for Arelle environment (SECWS, cmd line, GUI)
    # filer_data is None in transformation mode, only available in CGI mode
    instancesReports = filingSummaryParsed["instancesReports"]
    # Extract key fields for breadcrumbs and alias_path
    filename = ''
    if filer_data and isinstance(filer_data, list) and filer_data:
        first_filer = filer_data[0]
        filename = first_filer.get('filename', '')

    # Helper: Categorize reports (uses your categorize_report function)
    def categorize_report_xslt_style(instanceReports, report):
        # Refined mapping based on XSLT and sample XMLs
        long_name = (report.findtext('LongName', '') or '')
        menu_category = report.findtext('MenuCategory', default='')
        role = (report.findtext('Role', '') or '').lower() # part of URI is case insensitive
        doctype = (report.findtext('doctype', '') or '')
        ir = instanceReports
        cat = None

        # Uncategorized (template isUncategorized, variable is8 in xslt)
        if long_name == 'Uncategorized Items' or role == 'http://xbrl.sec.gov/role/uncategorizedfacts':
            cat = 'Uncategorized'
        # Risk/Return (template isRiskReturn, variable isRiskReturn in xslt)
        elif menu_category == 'Risk/Return':
            cat = 'Risk/Return'
        # template isDetail, variable is5 in xslt
        elif re.match(r".+- [^ -]+ - \(Detail", long_name):
            if ir.get("isDefinitelyNotFs"):
                cat = "Details"
            else:
                cat = "Notes Details"
        # Tables (template isTable, variable is4 in xslt)
        elif re.match(r".+- \w+ - \(Table", long_name):
            if ir.get("isDefinitelyNotFs"):
                cat = 'Tables'
            else:
                cat = "Notes Tables"
        # Policies (template isPolicy, variable is3 in xslt)
        elif re.match(r".+- \w+ - \(Polic", long_name):
            cat = 'Accounting Policies'
        # Disclosures (template isDisclosure, variable is2 in xslt)
        elif re.match(r".+- Disclosure - .", long_name):
            # xslt default_menu_group_title
            if ir.get("isRr"):
                cat = "Risk/Return Reports"
            elif ir.get("isn2prospectus") or ir.get("isn3n4n6"):
                cat = "Prospectus"
            elif ir.get("isfeeexhibit") or 'xbrl.sec.gov/ffd/' in role:
                cat = "Fee Exhibit"
            elif ir.get("isOnlyShr"):
                cat = "Repurchases"
            elif ir.get("isDefinitelyFs"):
                cat = "Notes to the Financial Statements"
            else:
                cat = "Reports"
        # Cover (template isDocument, variable is1)
        elif re.match(r".+- Document - .", long_name):
            if False: # menu_category == "Cover": WH note - you never do cover here
                cat = 'Cover'
            else:
                cat = 'Reports'
        # Statements (template isStatement, variable is0)
        elif re.match(r".+- Statement - .", long_name):
            if ir.get("isDefinitelyNotFs"):
                cat = 'Statements'
            else:
                cat = 'Financial Statements'
        elif menu_category == 'Uncategoriaed':
            cat = 'Other'
        elif menu_category == "Cover":
            cat = 'Cover'
        elif menu_category == "":
            cat = 'Cover'
        # Other
        else:
            cat = 'Other'
        log_debug(f"Categorized as {cat}: long {long_name} cat {menu_category} docT {doctype}")
        return cat

    def group_reports_xslt_style(instanceReports):
        groups = []
        current_category = None
        current_group = []

        for report in instanceReports["reports"]:
            category = categorize_report_xslt_style(instanceReports, report)
            if category != current_category:
                if current_group:
                    groups.append([current_category, current_group])
                current_category = category
                current_group = [report]
            else:
                current_group.append(report)
        if current_group:
            groups.append([current_category, current_group])
        return groups


    def choose_group_label(category, all_categories):
        known_labels = {
            "Cover", "Statements", "Notes", "Tables", "Details", "Policies",
            "Risk/Return", "Prospectus", "Fee Exhibit", "Uncategorized"
        }
        if category not in known_labels:
            if len(all_categories) == 1:
                return "Reports"
            else:
                return "Other"
        return category

    # Print Document link
    def build_print_link():
        print_link = html.Element('a', {
            'class': 'xbrlviewer',
            'style': 'color: black; font-weight: bold; ',
            'href': 'javascript:window.print()'
        })
        print_link.text = "Print Document"
        return print_link

    # Inline XBRL viewer link (first menu entry if present)
    def build_ixviewer_link(reports):
        for report in reports:
            is_inline = report.get('isinline', 'false') == 'true'
            original = report.get('original', '')
            doctype = report.get('doctype', '')
            if is_inline and original:
                ixviewer_url = f"/ix?doc={alias_path}/{original}"
                li_ix = html.Element('li', {'class': 'accordion ix'})
                a_ix = html.Element('a', {
                    'href': ixviewer_url,
                    'style': 'text-decoration: none;'
                })
                # Button with doctype label
                button = html.Element('button', {
                    'type': 'button',
                    'class': 'btn btn-warning',
                    'style': 'margin: 2px 0; font-size: 0.95em;'
                })
                button.text = doctype if doctype else "Inline XBRL Viewer"
                a_ix.append(button)
                li_ix.append(a_ix)
                return li_ix
        return None

    # All Reports link at the bottom (not indented)
    def build_all_reports_link():
        report_files = []
        for instanceReports in instancesReports.values():
            for report in instanceReports["reports"]:
                report_file = report.findtext('XmlFileName', default='') or report.findtext('HtmlFileName', default='')
                if report_file:
                    report_files.append(report_file)
        li_all = html.Element('li')
        a_all = html.Element('a', {
            'class': 'all_reports',
            'href': '#',
            'data-alias_path': alias_path,
            'data-report_files': ','.join(report_files),
            'style': 'font-weight: bold; background-color: #0C213A;'
        })
        imgElt = html.Element('img', {
            'src': '/images/reports.gif',
            'border': '0',
            'height': '12',
            'width': '9',
            'alt': 'Reports'
        })
        imgElt.tail = "All Reports"
        a_all.append(imgElt)
        li_all.append(a_all)
        return li_all

    # Accordion menu construction
    def build_menu():
        ul_menu = html.Element('ul', {'id': 'menu'})
        # 1. Print Document link
        # 2. Inline XBRL viewer link (if present)
        for instance, instanceReports in instancesReports.items():
            reports = instanceReports["reports"]
            ix_link = build_ixviewer_link(reports)
            if ix_link is not None:
                ul_menu.append(ix_link)
            # 3. Accordion categories
            groups = group_reports_xslt_style(instanceReports)
            all_categories = [cat for (cat, items) in groups]
            # WH note - don't what this behavior (from sec.gov vs XSLT)
            #if len(groups) == 2 and groups[0][0] == "Cover" and len(groups[0][1]) == 1 and groups[1][0] not in {
            #    "Statements", "Notes", "Tables", "Details", "Policies",
            #    "Risk/Return", "Prospectus", "Fee Exhibit", "Uncategorized"}:
            #    # move cover report in with the other categories reports
            #    groups[1][1].insert(0, groups[0][1][0])
            #    del groups[0]

            for cat, items in groups:
                li_cat = html.Element('li', {'class': 'accordion'})
                a_cat = html.Element('a', {
                    'id': f"menu_cat_{cat.replace(' ', '_')}",
                    'href': '#'
                })
                a_cat.text = cat # choose_group_label(cat, all_categories)
                li_cat.append(a_cat)
                ul_items = html.Element('ul')
                for report in items:
                    short_name = report.findtext('ShortName', default='') or report.findtext('LongName', default='')
                    report_file = report.findtext('XmlFileName', default='') or report.findtext('HtmlFileName', default='')
                    li_item = html.Element('li')
                    a_item = html.Element('a', {
                        'class': 'xbrlviewer',
                        'href': '#',
                        'data-alias_path': alias_path,
                        'data-report_file': report_file
                    })
                    a_item.text = short_name
                    li_item.append(a_item)
                    ul_items.append(li_item)
                li_cat.append(ul_items)
                ul_menu.append(li_cat)
        # 4. All Reports link at the bottom
        ul_menu.append(build_all_reports_link())
        return etree.tostring(ul_menu, pretty_print=True, method='html', encoding='unicode')

    # Company header above the table
    def build_company_header(filer_data):
        if not filer_data:
            return html.Element('div')
        filer = filer_data[0] if isinstance(filer_data, list) else filer_data
        header_div = html.Element('div', {
            'class': 'companyInfo',
            'style': 'margin-bottom: 10px; font-size: 1.2em; font-weight: bold;'
        })
        company_name = filer.get('conformed_name', '')
        cik = filer.get('cik', '')
        span_company = html.Element('span', {'class': 'companyName'})
        span_company.text = company_name
        if cik:
            span_company.text += " (Filer) "
            acronym = html.Element('acronym', title="Central Index Key")
            acronym.text = "CIK"
            acronym.tail = f": {cik}"
            span_company.append(acronym)
        header_div.append(span_company)
        return header_div

    def build_company_info_section(filer_data):

        # Outer wrapper divs
        content_div = html.Element('div', {'id': 'contentDiv'})

        # Company info (your existing logic, simplified here)
        for filer in filer_data if isinstance(filer_data, list) else [filer_data]:
            filer_div = html.Element('div', {'class': 'FilerDiv'})
            company_info = html.Element('div', {'class': 'companyInfo'})

            # Company Name
            span_company = html.Element('span', {'class': 'companyName'})
            span_company.text = filer.get('conformed_name', '')

            # CIK with acronym and browseEdgar link
            cik = filer.get('cik', '')
            if cik:
                span_company.text += " (Filer) "
                acronym = html.Element('acronym', title="Central Index Key")
                acronym.text = "CIK"
                acronym.tail = ": "
                span_company.append(acronym)
                cik_link = html.Element('a', {
                    'href': f'/cgi-bin/browse-edgar?CIK={cik}&action=getcompany',
                    'target': '_blank',
                    'style': 'text-decoration: underline; color: #0074d9;'
                })
                cik_link.text = f"{cik} (see all company filings)"
                span_company.append(cik_link)
            company_info.append(span_company)
            company_info.append(html.Element('br'))

            p_ident = html.Element('p', {'class': 'identInfo'})
            company_info.append(p_ident)
            p_elt = p_ident

            # IRS, State, Fiscal Year
            if filer.get('irs_number', ''):
                acronym = html.Element('acronym', title="Internal Revenue Service Number")
                acronym.text = "IRS No."
                acronym.tail = ": "
                p_ident.append(acronym)
                p_elt = html.Element('strong')
                p_elt.text=filer.get("irs_number", "")
                p_ident.append(p_elt)
            if filer.get('state_of_incorporation', ''):
                p_elt.tail = " | State of Incorp.: "
                p_elt = html.Element('strong')
                p_elt.text=filer.get("state_of_incorporation", "")
                p_ident.append(p_elt)
            if filer.get('fiscal_year_end', ''):
                p_elt.tail = " | Fiscal Year End.: "
                p_elt = html.Element('strong')
                p_elt.text=filer.get("fiscal_year_end", "")
                p_ident.append(p_elt)
            p_elt = html.Element('br')
            p_ident.append(p_elt)

            if 'filing_info' in filer and filer['filing_info']:
                filing_info = filer['filing_info'][0] if isinstance(filer['filing_info'], list) else filer['filing_info']
            if filing_info:
                # Type, Act, File No, Film No
                if filing_info.get('form_type'):
                    p_elt.tail = "Type: "
                    p_elt = html.Element('strong')
                    p_elt.text=filing_info['form_type']
                    p_ident.append(p_elt)
                if filing_info.get('act'):
                    p_elt.tail = " | Act: "
                    p_elt = html.Element('strong')
                    p_elt.text=filing_info['act']
                    p_ident.append(p_elt)
                if filing_info.get('file_number'):
                    p_elt.tail = " | File No.: "
                    p_elt = html.Element('a', {
                        'href': f'/cgi-bin/browse-edgar?filenum={filing_info["file_number"]}&action=getcompany'
                    })
                    p_elt.text=filing_info["file_number"]
                    p_ident.append(p_elt)
                if filing_info.get('film_number'):
                    p_elt.tail = f"| Film No.: {filing_info['film_number']}"
            # SIC code and description
            if filer.get('assigned_sic'):
                sic = filer['assigned_sic']
                p_elt = html.Element('br')
                p_ident.append(p_elt)
                p_elt = html.Element('acronym', title="Standard Industrial Code")
                p_elt.text="SIC"
                p_ident.append(p_elt)
                p_elt.tail = ": "
                p_elt = html.Element('a', {
                    'href': f'/cgi-bin/browse-edgar?SIC={sic}&action=getcompany&owner=include'
                })
                p_elt.text = sic
                p_ident.append(p_elt)
                if sic in sic_codes:
                    p_elt.tail = f"  {sic_codes[sic]}"

            # Owner Org
            if filer.get('owner_org', ''):
                p_elt = html.Element('br')
                p_ident.append(p_elt)
                p_elt.tail = f"(CF Office: {filer.get('owner_org', '')})"

            # Mailing Address
            mailer_div = html.Element('div', {'class': 'mailer'})
            mailer_div.text = "Mailing Address"
            for field in ['m_street1', 'm_street2']:
                if filer.get(field, ''):
                    span_mail = html.Element('span', {'class': 'mailerAddress'})
                    span_mail.text = filer.get(field, '')
                    mailer_div.append(span_mail)
            city_state_zip = ' '.join([filer.get('m_city', ''), filer.get('m_state', ''), filer.get('m_zip', '')]).strip()
            if city_state_zip:
                span_mail = html.Element('span', {'class': 'mailerAddress'})
                span_mail.text = city_state_zip
                mailer_div.append(span_mail)
            ''' there is no m_phone in filer table
            if filer.get('m_phone', ''):
                span_mail = html.Element('span', {'class': 'mailerAddress'})
                span_mail.text = filer.get('m_phone', '')
                mailer_div.append(span_mail)
            filer_div.append(mailer_div)
            '''

            # Business Address
            business_div = html.Element('div', {'class': 'mailer'})
            business_div.text = "Business Address"
            for field in ['street1', 'street2']:
                if filer.get(field, ''):
                    span_bus = html.Element('span', {'class': 'mailerAddress'})
                    span_bus.text = filer.get(field, '')
                    business_div.append(span_bus)
            city_state_zip = ' '.join([filer.get('city', ''), filer.get('state', ''), filer.get('zip', '')]).strip()
            if city_state_zip:
                span_bus = html.Element('span', {'class': 'mailerAddress'})
                span_bus.text = city_state_zip
                business_div.append(span_bus)
            if filer.get('phone', ''):
                span_bus = html.Element('span', {'class': 'mailerAddress'})
                span_bus.text = filer.get('phone', '')
                business_div.append(span_bus)
            filer_div.append(business_div)

            filer_div.append(company_info)

            # Clear div
            clear_div = html.Element('div', {'class': 'clear'})
            filer_div.append(clear_div)
            content_div.append(filer_div)

        return content_div

    def build_footer_section():

        # Outer wrapper divs
        footer_div = html.Element('div', {'id': 'footer'})

        currentURL_div = html.Element('div', {'class': 'currentURL'})
        currentURL_div.text = 'https://www.sec.gov/cgi-bin/viewer'
        footer_div.append(currentURL_div)

        links_div = html.Element('div', {'class': 'links'})
        for href, text, tail in (('/index.htm', 'Home', ' | '),
                                 ('/edgar/searchedgar/webusers.htm', 'Search the Next-Generation EDGAR System', ' | '),
                                 ('javascript:history.back()', 'Previous Page', None)):
            link_a = html.Element('a', {'href': href})
            link_a.text = text
            if tail:
                link_a.tail = tail
            links_div.append(link_a)
        footer_div.append(links_div)

        modified_div = html.Element('div', {'class': 'modified'})
        modified_div.text = 'Modified 10/31/2025'
        footer_div.append(modified_div)

        return footer_div

    # Find first report URL for auto-load
    first_report_file = ''
    for instanceReports in instancesReports.values():
        for report in instanceReports["reports"]:
            first_report_file = report.findtext('XmlFileName', default='') or report.findtext('HtmlFileName', default='')
            if first_report_file: break
        if first_report_file: break

    # Start HTML doc
    doc = html.Element('html', lang='en')
    head = html.Element('head')
    doc.append(head)
    head.append(html.Element('meta', charset='UTF-8'))
    title = html.Element('title')
    title.text = "View Filing Data"
    head.append(title)

    # jQuery and other scripts
    if mode == "server":
        scripts = [
            ("/js/third-party/jquery-latest.min.js", "text/javascript"),
            ("/include/accordionMenu.js", "text/javascript"),
            ("/include/Show.js", "text/javascript"),
        ]
    else: # mode == transform
        scripts = [
            ("/include/jquery-3.7.1.min.js", "text/javascript"),
            ("/include/accordionMenu.js", "text/javascript"),
            ("/include/Show.js", "text/javascript"),
        ]
    for src, typ in scripts:
        script_tag = html.Element('script', type=typ, src=src)
        head.append(script_tag)

    # Stylesheets
    if mode == "server":
        stylesheets = [
            ("/include/interactive2.css", "text/css", None),
            ("/edgar/search/global/css/bootstrap/bootstrap.min.css", "text/css", None),
            ("/include/report.css", "text/css", None),
            ("/include/print.css", "text/css", "print"),
            ("/include/xbrlViewerStyle.css", "text/css", None),
        ]
    else: # mode == transform
        stylesheets = [
            ("/include/interactive.css", "text/css", None),
            ("/include/report.css", "text/css", None),
            ("/include/print.css", "text/css", "print"),
        ]
    for href, typ, media in stylesheets:
        link_tag = html.Element('link', rel="stylesheet", type=typ, href=href)
        if media:
            link_tag.set("media", media)
        head.append(link_tag)

    # Inline jQuery script for dynamic report loading and All Reports
    jquery_script = f"""
    $(document).ready(function() {{
        // Accordion expand/collapse (accordionMenu.js should handle this)
        // AJAX report loading for individual reports
        $('#menu').on('click', '.xbrlviewer', function(e) {{
            e.preventDefault();
            var alias_path = $(this).data('alias_path');
            var report_file = $(this).data('report_file');
            if (report_file) {{
                $('#reportDiv').html('<div style="text-align:center;">Loading...</div>');
                $.ajax({{
                    url: alias_path ? (alias_path + '/' + report_file) : report_file,
                    type: 'GET',
                    dataType: 'html',
                    success: function(data) {{
                      // Strip out everything between the "TEXT" elements
                      var idx = data.indexOf('<TEXT>');
                      if (idx > -1) {{
                         data = data.substring(idx+6,data.length);
                         idx = data.indexOf('</TEXT>');
                         if ( idx > -1) {{
                            data = data.substring(0,idx);
                         }}
                      }}
                      jQuery('#reportDiv').html(data)
                        .find('img').attr('src', function(i, val) {{ return fixSrcAttr(val,alias_path);}}).end();
                    }},
                    error: function() {{
                        $('#reportDiv').html('<div style="color:red;">Failed to load report.</div>');
                    }}
                }});
            }}
            $('.xbrlviewer').css('background', '#F5F5EB');
            $('.all_reports').css('background', '#0C213A');
            $(this).css('background', '#C1CDCD');
        }});
        // AJAX loading for All Reports
        $('#menu').on('click', '.all_reports', function(e) {{
            e.preventDefault();
            var alias_path = $(this).data('alias_path');
            var report_files = $(this).data('report_files');
            if (report_files) {{
                var report_files_list = report_files.split(',');
                $('#reportDiv').html('<div style="text-align:center;">Loading all reports...</div>');
                var allHtml = '';
                var loaded = 0;
                report_files_list.forEach(function(report_file) {{
                    $.ajax({{
                        url: alias_path ? (alias_path + '/' + report_file) : report_file,
                        type: 'GET',
                        dataType: 'html',
                        success: function(data) {{
                            // Strip out everything between the "TEXT" elements
                            var idx = data.indexOf('<TEXT>');
                            if (idx > -1) {{
                              data = data.substring(idx+6,data.length);
                              idx = data.indexOf('</TEXT>');
                              if ( idx > -1) {{
                                data = data.substring(0,idx);
                              }}
                            }}
                            allHtml += data + '<hr>';
                            loaded++;
                            if (loaded === report_files_list.length) {{
                                $('#reportDiv').html(allHtml)
                                   .find('img').attr('src', function(i, val) {{ return fixSrcAttr(val,alias_path);}}).end()
                            }}
                        }},
                        error: function() {{
                            allHtml += '<div style="color:red;">Failed to load report: ' + url + '</div><hr>';
                            loaded++;
                            if (loaded === urlList.length) {{
                                $('#reportDiv').html(allHtml);
                            }}
                        }}
                    }});
                }});
            }}
            $('.xbrlviewer').css('background', '#F5F5EB');
            $(this).css('background', '#818D8D');
        }});
        // On page load, trigger click on the first report
        var firstReportFile = "{first_report_file}";
        if (firstReportFile) {{
            var firstLink = $('.xbrlviewer[data-report_file="' + firstReportFile + '"]');
            if (firstLink.length) {{
                firstLink.trigger('click');
            }}
        }}
    }});


   function fixSrcAttr(src, alias_path) {{
      var uri = src.substr(0,5);
      // No change is needed if the 'src' attribute contains an embedded image
      if (uri == 'data:') {{
         return src;
      }}
      // Absolute URL on EDGAR website is unchanged
      var idx = src.lastIndexOf('https://s3.amazonaws.com/archives.sec.gov/edgar/data/')
      if (idx > -1) {{
        return src;
      }} // For all other URLs use only basename component
      var idx = src.lastIndexOf('/');
      if (idx > -1) {{
         src = src.substring(idx+1,src.length);
      }}
      return alias_path ? (alias_path + '/' + src) : src;
   }}

    """
    script_tag = html.Element('script', type="text/javascript")
    script_tag.text = jquery_script
    head.append(script_tag)

    # Inline style for body (optional)
    style = html.Element('style')
    style.text = """
    body { font-family: Arial, sans-serif; margin: 20px; }
    .companyInfo, .filerDiv { margin-bottom: 20px; }
    .menu { background: #f5f5f5; padding: 10px; margin-bottom: 20px; }
    .report { border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px; }
    .companyHeader { margin-bottom: 10px; font-size: 1.2em; font-weight: bold; }
    """
    head.append(style)

    # Body
    body = html.Element('body')
    doc.append(body)

    if filer_data: # CGI mode
        # Banner
        body.append(build_banner())

        # Breadcrumbs
        body.append(build_breadcrumbs(cik, accession_number, accession_number_dashed, filename))

        # Error messages
        if errors:
            error_html = build_error_html(errors)
            body.append(html.fromstring(error_html))

        # Company header above the table
        body.append(build_company_header(filer_data))

    # Print function
    body.append(build_print_link())

    # Main content: two-column layout (accordion menu left, report pane right)
    table = html.Element('table')
    tr = html.Element('tr')
    td_menu = html.Element('td', style="vertical-align: top;")
    menu_div = html.Element('div', style="width: 170px; margin-right: 5px;")
    td_menu.append(menu_div)
    menu_div.append(html.fromstring(build_menu()))
    td_report = html.Element('td', style="vertical-align: top;")
    report_div = html.Element('div', {'id': 'reportDiv'})
    td_report.append(report_div)
    tr.append(td_menu)
    tr.append(td_report)
    table.append(tr)
    body.append(table)

    if filer_data: # CGI mode
        # Add company info and footer sections
        body.append(build_company_info_section(filer_data))
        body.append(build_footer_section())

    return doc

def secure_field(dirty_string):
    return re.sub(r"[^A-Za-z0-9,./?:#@\-_=+\s'\"()$%\x96\x97\xAE]", "", dirty_string)

# --- Arelle EDGAR/render FilingSummary.xml to html transformation --
def transformToHtml(filingSummaryEtree, accession_number):
    # note alias_path is not set (empty string) for Arelle GUI operation
    global IS_DEV_ENV
    IS_DEV_ENV = 0 # cgi-bin debug options inapplicable to Arelle EDGAR plugin use, disable log_debug
    filingSummaryParsed = parse_reports(filingSummaryEtree)
    html_doc = build_html("transform", None, accession_number, '', '', None, filingSummaryParsed, None)
    return html_doc

# --- Main CGI Handler ---
def main():
    global alias_path
    log_debug(f"****** Viewer.py CGI at {datetime.now().isoformat()} ******")
    print("Content-Type: text/html\n")
    # Command-line argument support for dev mode
    if IS_DEV_ENV and len(sys.argv) > 1:
        query_dict = dict(p.split("=", 1) for p in sys.argv[1:] if "=" in p)
        os.environ['QUERY_STRING'] = urllib.parse.urlencode(query_dict)
        os.environ['REQUEST_METHOD'] = 'GET'
    form = cgi.FieldStorage()
    accession_number_dashed = secure_field(form.getfirst('accession_number', ''))
    log_debug(f"acc nmbr dashed {accession_number_dashed}")
    if "-" not in accession_number_dashed:
        accession_number_dashed = f"{accession_number_dashed[:10]}-{accession_number_dashed[10:12]}-{accession_number_dashed[12:]}"
    log_debug(f"acc nmbr dashed {accession_number_dashed}")
    accession_number = re.sub(r"-", "", accession_number_dashed) # strip dashes from cik
    cik = secure_field(form.getfirst('cik', ''))
    cik = re.sub(r"^0+", "", cik) # strip leading zeros from cik
    db_connection = None
    if IS_DEV_ENV in (0, 3):
        log_debug("opening mysql connector")
        import mysql.connector
        db_connection = mysql.connector.connect(
            host='localhost',
            port='3307',
            user='dev',
            password='WWdev9876!',
            database='edgardb'
        )
        log_debug("opened mysql connector")
    filer_data, errors = get_filer_data(accession_number_dashed, db_connection)
    if db_connection:
        db_connection.close()
        db_connection = None # dereference
    filer_data = filer_data
    log_debug(filer_data)
    alias_path = f"{FILING_DATA_PATH}/{cik}/{accession_number}"
    filingSummaryParsed = parse_reports(f"{alias_path}/FilingSummary.xml")
    try:
        html_doc = build_html("server", cik, accession_number, accession_number_dashed, alias_path, filer_data, filingSummaryParsed, errors)
        html_content = etree.tostring(html_doc, pretty_print=True, method='html', encoding='unicode')
        print(html_content)
    except Exception as ex:
        log_debug(f"Exception in html generation, traceback: {traceback.format_exception(*sys.exc_info())}")

if __name__ == "__main__":
    main()
