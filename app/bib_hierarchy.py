import io
import xml.etree.ElementTree as ET

import requests
import pymarc
import natsort

class BibHierarchy (object):

    def __init__(self, acnr, institution_code="43ACC_UBG"):
        self.acnr = acnr
        self.institution_code = institution_code
        self.records = self.__get_records(acnr)
        if self.records:
            self.head, self.deps = self.__build_hierarchy(self.records)
            # bring self.records in the right order after determining it
            self.records = [self.head[3]] + [dep[3] for dep in self.deps]

    def __get_records(self, acnr):
        """Get all records containing acnr and return a list of pymarc.Record objects."""

        # Namespaces for the responses from Alma
        ns = {'marc': 'http://www.loc.gov/MARC21/slim',
              'srw': 'http://www.loc.gov/zing/srw/'}
        # Template für MARC-XML
        marc_template = """<marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"/>"""
        xml_records = ET.fromstring(marc_template)

        # get the records from Alma
        offset = 1
        sru_request = "https://obv-at-obvsg.alma.exlibrisgroup.com/view/sru/43ACC_NETWORK?version=1.2&operation=searchRetrieve&recordSchema=marcxml&query=other_system_number={acnr}&startRecord={offset}&maximumRecords=50"
        # sru_request = "https://obv-at-obvsg.alma.exlibrisgroup.com/view/sru/43ACC_UBG?version=1.2&operation=searchRetrieve&recordSchema=marcxml&query=other_system_number={acnr}&startRecord={offset}&maximumRecords=50"

        # get the first 50 records
        res = requests.get(sru_request.format(acnr=acnr, offset=offset))

        # check how many records there are. If there are none, return None
        res_xml = ET.fromstring(res.text)
        numberOfRecords = int(res_xml.find("srw:numberOfRecords", ns).text)
        if numberOfRecords == 0:
            return None

        # add the records to the record list
        for record in res_xml.findall('.//marc:record', ns):
            xml_records.append(record)

        # repeat the request with increasing offset to get all records
        while offset < numberOfRecords - 50:
            offset += 50
            res = requests.get(sru_request.format(acnr=acnr, offset=offset))
            res_xml = ET.fromstring(res.text)
            # add the records to the record list
            for record in res_xml.findall('.//marc:record', ns):
                xml_records.append(record)

        # convert xml element to file-like-object, so pymarc can parse it
        marcfile = io.StringIO(ET.tostring(xml_records, encoding="unicode"))

        # parse the xml to a pymarc.Reader and make a list of pymarc.Records
        with marcfile as marcfile:
            reader = pymarc.parse_xml_to_array(marcfile)
            pymarc_records = []
            for record in reader:
                pymarc_records.append(record)

        return pymarc_records


    def __build_hierarchy(self, record_list):
        """Return a tuple with the head of the hierarchy and the
        dependent records as a list.

        Each element in the List is a tuple (numbering, year, network number,
        pymarc.Record).
        """

        order = []

        for rec in record_list:
            field_009 = rec["009"].value().strip()
            year = rec["008"].data[7:11]
            if field_009 == self.acnr:
                head = ("_head", year, field_009, rec)
            else:
                # get the sorting from 773 if it's a dependent title
                for field in rec.get_fields("773"):
                    if self.acnr in field.value():
                        if field["q"]:
                            order.append((field["q"], year, field_009, rec))
                        else:
                            order.append(("???", year, field_009, rec))

                # get the sorting from 830 if it's an independent title
                for field in rec.get_fields("830"):
                    if self.acnr in field.value():
                        if field["v"]:
                            order.append((field["v"], year, field_009, rec))
                        else:
                            order.append(("???" , year, field_009, rec))

        return head, natsort.natsorted(order)


    # helper functions
    def __check_rectype(self, record):
        """Check if a record is a TAT, a TUT or a MTM and return a corresponding
        string.
        """

        if record.leader[19] == "c":
            rectype = "TAT"
        elif record.leader[19] == "b":
            rectype = "TUT"
        elif record.leader[19] == "a":
            rectype = "MTM"
        else:
            rectype = None

        return rectype

    def __check_holdings(self, record, institution_code):
        """Return true, if institution has holdings for the record"""

        holdings = False
        for field in record.get_fields("852"):
            if institution_code in field["a"]:
                holdings = True

        return holdings

    def __build_title_string(self, rec, numbering, dep_type):
        """Return a string of the title with the right ISBD punctuation."""

        # if it's a dependent title, get rid of redundant information
        if dep_type == "TAT":
            title = rec["245"].subfields
            subfields = []
            sf_to_ignore = ["a", "b", "c"]

            skip = False
            first = True
            for subfield in title:
                if skip:
                    skip = False
                    continue

                if subfield in sf_to_ignore:
                    skip = True
                elif subfield == "n":
                    if first:
                        first = False
                    else:
                        subfields.append(". ")
                elif subfield == "p":
                    if first:
                        first = False
                    else:
                        subfields.append(", ")
                else:
                    subfields.append(subfield)

            titlestring = "".join(subfields)
        # else build the title with ISBD-punctuation
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

            if numbering == "_head":
                titlestring = "".join(subfields)
            else:
                titlestring = numbering + ": " + "".join(subfields)

        return titlestring

    def as_string(self):
        """Return a string with a representation of the hierarchy."""

        lst = self.as_list_of_dicts()

        s = f'{lst[0]["title"]}\n    {lst[0]["date"]}\n'
        if lst[0]["edition"]:
            s += f"    Ausgabe: {lst[0]['edition']}\n"
        s += f"    Netzwerk-ID: {lst[0]['network_id']}\n\n"

        s += f"    {len(self.deps)} abhängige Datensätze\n\n"

        # iterate over all dependent records in the right order
        for dep in lst:
            tut_prefix = "    |===> "
            tat_prefix = "    |---> "
            general_prefix = "    |     "
            # check if in IZ
            if dep["has_holdings"]:
                tut_prefix = "*   |===> "
                tat_prefix = "*   |---> "
                general_prefix = "    |     "

            # add the title with the right prefix
            if dep["dep_type"] == "TAT":
                s += tat_prefix + dep["title"] + "\n"
            else:
                s += tut_prefix + dep["title"] + "\n"

            if dep["edition"]:
                s += general_prefix + f'    Auflage: {dep["edition"]}\n'
            if dep["date"]:
                s += general_prefix + f'    Erscheinungsdatum: {dep["date"]}\n'
            s += general_prefix + f'    Netzwerk-ID: {dep["network_id"]}\n'

        return s

    def as_list(self):
        """Return the hierarchy in a list. The first Element is the head of the
        hierarchy, the subsequent elements are the dependent records.

        Each element in the List is a dict
        {"dep_type": str,
         "numbering": str,
         "title": str,
         "date": str,
         "edition": str,
         "network_id": str,
         "has_holdings": boolean}

        """

        lst = []
        # head = ("head", year, field_009, rec)
        def build_dict(self, rec):
            dct = {}
            marc = rec[3]
            # dep_type
            if rec[0] == "_head":
                dct["dep_type"] = "head"
            else:
                dct["dep_type"] = self.__check_rectype(marc)

            dct["numbering"] = rec[0]
            dct["title"] = self.__build_title_string(marc, rec[0], dct["dep_type"])
            if marc["264"]:
                if marc["264"]["c"]:
                    dct["date"] = marc["264"]["c"]
                else:
                    dct["date"] = "[Kein Erscheinungsdatum vorhanden]"
            if marc["250"]:
                dct["edition"] = marc["250"].value()
            else:
                dct["edition"] = None
            dct["network_id"] = rec[2]
            dct["has_holdings"] = self.__check_holdings(marc, self.institution_code)

            return dct

        for rec in [self.head] + self.deps:
            lst.append(build_dict(self, rec))

        return lst

