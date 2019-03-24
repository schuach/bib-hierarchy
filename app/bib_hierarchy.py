import requests
import urllib.parse
import io
import pymarc
import xml.etree.ElementTree as ET
import sys
import natsort
import os
import easygui
def get_user_input():
    title = "ALMA Hierarchieabfrage"
    msg = "Bitte die AC-Nummer des Kopfsatzes eingeben."

    acnr = easygui.enterbox(msg, title)

    return acnr
# Namespaces fürs xml
ns = {'marc': 'http://www.loc.gov/MARC21/slim', 'srw': 'http://www.loc.gov/zing/srw/'}
# Template für MARC-XML
marc_template = """<marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"/>"""

institution_code = "43ACC_UBG"
# get the network number from the user
if len(sys.argv) == 1:
    acnr = get_user_input()
else:
    acnr = sys.argv[1]

def get_records(acnr):
    """Get all records containing acnr and return a list of responses (strings)"""
    response_list = []
    offset = 1
    # sru_request = "https://obv-at-ubg.alma.exlibrisgroup.com/view/sru/43ACC_UBG?version=1.2&operation=searchRetrieve&recordSchema=marcxml&query=other_system_number={acnr}&startRecord={offset}&maximumRecords=50"
    sru_request = "https://obv-at-obvsg.alma.exlibrisgroup.com/view/sru/43ACC_NETWORK?version=1.2&operation=searchRetrieve&recordSchema=marcxml&query=other_system_number={acnr}&startRecord={offset}&maximumRecords=50"

    # get the first 50 records
    res = requests.get(sru_request.format(acnr=acnr, offset=offset))
    # append the response to the list
    response_list.append(res.text)

    # check how many records there are
    res_xml = ET.fromstring(res.text)
    numberOfRecords = int(res_xml.find("srw:numberOfRecords", ns).text)data

    if numberOfRecords == 0:
        ret_val = easygui.msgbox("Keine Datensätze gefunden.")
        if ret_val is None:
            quit()

    # repeat the request with increasing offset to get all records
    while offset < numberOfRecords - 50:
        offset += 50
        res = requests.get(sru_request.format(acnr=acnr, offset=offset))
        response_list.append(res.text)

    return response_list
def populate_reclist(response_list):
    """Populate a list with the records containing acnr."""

    reclist = []
    marc_xml = ET.fromstring(marc_template)

    # append all the marc-records in the responses to marc_xml
    for response in response_list:
        res_xml = ET.fromstring(response)
        for record in res_xml.findall('.//marc:record', ns):
            marc_xml.append(record)

    # convert xml element to file-like-object, so pymarc can parse it
    marcfile = io.StringIO(ET.tostring(marc_xml, encoding="unicode"))

    # parse the xml to a pymarc.Reader
    with marcfile as marcfile:
        reader = pymarc.parse_xml_to_array(marcfile)

    for record in reader:
        reclist.append(record)

    return reclist
def build_hierarchy(record_list):
    hierarchy = {"head": None, "deps": {}, "order": {}}

    for rec in record_list:
        field_009 = rec["009"].value().strip()
        if field_009 == acnr:
            hierarchy["head"] = rec
        else:
            hierarchy["deps"][field_009] = rec
            for field in rec.get_fields("773"):
                if not acnr in field.value():
                    continue
                else:
                    if field["q"] == None:
                        field.add_subfield("q", "ZZZ - Keine Sortieform vorhanden")
                    if not field["q"] in hierarchy["order"]:
                        hierarchy["order"][field["q"]] = [field_009]
                    else:
                        hierarchy["order"][field["q"]].append(field_009)

            for field in rec.get_fields("830"):
                if not acnr in field.value():
                    continue
                else:
                    if field["v"] == None:
                        field.add_subfield("v", "ZZZ - Keine Sortieform vorhanden")
                    if not field["v"] in hierarchy["order"]:
                        hierarchy["order"][field["v"]] = [field_009]
                    else:
                        hierarchy["order"][field["v"]].append(field_009)

    return hierarchy
def check_rectype(record):
    """Check if a record is a TAT or a TUT and return corresponding string."""

    if record.leader[19] == "c":
        rectype = "TAT"
    elif record.leader[19] == "b":
        rectype = "TUT"
    # TODO check for MTM
    else:
        rectype = None

    return rectype

def check_holdings(record, institution_code):
    "Return true, if institution has holdings for the record"

    holdings = False
    for field in record.get_fields("852"):
        if institution_code in field["a"]:
            holdings = True
        else:
            continue

    return holdings
def print_hierarchy(hierarchy):


    print(hierarchy["head"]["245"].value())

    # make list of sorted keys for hierarchy["order"]
    order = natsort.natsorted(hierarchy["order"].keys())

    # iterate over all dependent records in the right order
    for keylist in order:
        # print(keylist)
        for key in hierarchy["order"][keylist]:
            rec = hierarchy["deps"][key]
            # checken if in IZ
            for field in rec.get_fields("852"):
                if check_holdings(rec, institution_code) is True:
                    tut_prefix = "*   |===> "
                    tat_prefix = "*   |---> "
                    general_prefix = "    |     " 
                else:
                    tut_prefix = "    |===> "
                    tat_prefix = "    |---> "
                    general_prefix = "    |     " 

            if check_rectype(rec) == "TAT":
                title = rec["245"].subfields
                subfields = []
                sf_to_delete = ["a", "b", "c"]

                # get rid of $$b and $$c
                for code in sf_to_delete:
                    if code in title:
                        index = title.index(code)
                        # once for the code
                        del title[index]
                        # and for the value
                        del title[index]

                for subfield in title[1:]:
                    if subfield == "n":
                        subfields.append(". ")
                    elif subfield == "p":
                        subfields.append(", ")
                    else:
                        subfields.append(subfield)

                titlestring = tat_prefix + "".join(subfields)
            else:
                title = rec["245"].subfields
                subfields = []

                for subfield in title:
                    if subfield == "a":
                        continue
                    elif subfield == "b":
                        subfields.append(" : ")
                    elif subfield == "c":
                        subfields.append(" / ")
                    else:
                        subfields.append(subfield)

                titlestring = tut_prefix + keylist + ": " + "".join(subfields)

            print(titlestring)
            if rec["250"]:
                print(general_prefix + f'    Auflage: {rec["250"]["a"]}')
            print(general_prefix + f'    Erscheinungsdatum: {hierarchy["deps"][key]["264"]["c"]}')
            print(general_prefix + f'    AC-Nummer: {key}')
def print_to_file(hierarchy, filename):
    stdout_ = sys.stdout
    f = open(filename, "w")
    sys.stdout = f
    print_hierarchy(hierarchy)
    sys.stdout = stdout_
    f.close()
    if os.name == "nt":
        os.startfile(filename)
def print_to_codebox(hierarchy):
    stdout_ = sys.stdout
    sys.stdout = mystdout = io.StringIO()
    print_hierarchy(hierarchy)
    sys.stdout = stdout_
    s = mystdout.getvalue()

    easygui.codebox(text=s)

response_list = get_records(acnr)
record_list = populate_reclist(response_list)
hierarchy = build_hierarchy(record_list)
print_to_codebox(hierarchy)
# print_to_file(hierarchy, "outfile.txt")
