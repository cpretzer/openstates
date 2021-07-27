from spatula import CSS, HtmlListPage, HtmlPage
from openstates.models import ScrapePerson
import re


class AdditionalAddresses(HtmlPage):
    # print("we get here")
    def process_page(self):
        p = self.input
        additional_office = (
            CSS("td.notranslate.member").match_one(self.root).text_content()
        )
        additional_office, additional_phone = additional_office.split("(")
        # print(additional_office)
        # print(additional_phone)

        p.additional_offices = additional_office
        p.extras["extra phone"] = additional_phone


class LegDetail(HtmlPage):
    def process_page(self):
        p = self.input

        img = CSS("body table tr td img").match(self.root)[2].get("src")
        p.image = img

        (
            capitol_addr,
            capitol_phone,
            capitol_fax,
            district_addr,
            district_phone,
            district_fax,
            email,
            # additional_office,
            # additional_phone
        ) = self.process_addrs(p)

        p.capitol_office.address = capitol_addr
        p.capitol_office.voice = capitol_phone
        if capitol_fax:
            p.capitol_office.fax = capitol_fax
        if district_addr:
            p.district_office.address = district_addr
        if district_phone:
            p.district_office.voice = district_phone
        if district_fax:
            p.district_office.fax = district_fax
        if email:
            p.email = email
        # if additional_office:
        #     p.additional_address = additional_office
        # if additional_phone:
        #     p.extras["extra phone"] = additional_phone

        return p

    def process_addrs(self, p):
        """
        For a given detail page, len(CSS("body table tr td.member").match(self.root))
        can be either 7, 10, 11, 12, 13, 14, or 15. This function / for loop handles
        pages with varies number of 'address' lines.
        """
        (
            capitol_addr,
            cap_phone,
            capitol_fax,
            district_addr,
            dis_phone,
            dis_fax,
            email,
            # additional_office,
            # additional_phone
        ) = (None, None, None, None, None, None, None)
        addresses = CSS("body table tr td.member").match(self.root)
        line_number = 0
        district_addr_lines = 0
        for line in addresses:
            if line.text_content().strip() == "Additional District Addresses":
                print("ADDITIONAL ADDRS")
                # additional_addr_link = line.getchildren()[0].get("href")
                # print(additional_addr_link)
                # AdditionalAddresses(p, source=additional_addr_link)

            line = line.text_content().strip()
            if (
                line == "Springfield Office:"
                or line == "District Office:"
                or line == ""
                or line == "Additional District Addresses"
                or line.startswith("Senator")
                or line.startswith("Representative")
                or line.startswith("Years served:")
            ):
                line_number += 1
                continue

            if not capitol_addr:
                capitol_addr = line
                line_number += 1
            elif line_number in [2, 3] and not line.startswith("("):
                capitol_addr += " "
                capitol_addr += line
                line_number += 1
            elif not cap_phone and line.startswith("("):
                cap_phone = line
                line_number += 1
            elif (line_number in [4, 5]) and re.search(r"FAX", line):
                capitol_fax = re.search(r"(.+)\sFAX", line).groups()[0]
                line_number += 1
            elif not district_addr:
                district_addr = line
                line_number += 1
                district_addr_lines += 1
            elif district_addr_lines == 1:
                district_addr += " "
                district_addr += line
                line_number += 1
                district_addr_lines += 1
            elif (
                district_addr_lines == 2
                and not line.strip().startswith("(")
                and not re.search(r"Email:", line)
            ):
                district_addr += " "
                district_addr += line
                line_number += 1
                district_addr_lines += 1
            elif not dis_phone:
                dis_phone = line
                line_number += 1
            elif re.search(r"FAX", line):
                dis_fax = re.search(r"(.+)\sFAX", line).groups()[0]
                line_number += 1
            elif re.search(r"Email:\s", line.strip()):
                email = re.search(r"Email:\s(.+)", line).groups()[0].strip()
                line_number += 1

        return (
            capitol_addr,
            cap_phone,
            capitol_fax,
            district_addr,
            dis_phone,
            dis_fax,
            email,
            # additional_office,
            # additional_phone
        )


class LegList(HtmlListPage):
    selector = CSS("form table tr")

    def process_item(self, item):
        # skip header rows
        if (
            len(CSS("td").match(item)) == 1
            or CSS("td").match(item)[0].get("class") == "header"
        ):
            self.skip()

        first_link = CSS("td a").match(item)[0]
        name = first_link.text_content()
        detail_link = first_link.get("href")

        # these are "Former Senate Members"
        former_members = [
            "Andy Manar",
            "Heather A. Steans",
            "Edward Kodatt",
            "Michael J. Madigan",
            "André Thapedi",
        ]
        if name in former_members:
            self.skip()

        district = CSS("td").match(item)[3].text_content()
        party_letter = CSS("td").match(item)[4].text_content()
        party_dict = {"D": "Democratic", "R": "Republican", "I": "Independent"}
        party = party_dict[party_letter]

        p = ScrapePerson(
            name=name,
            state="il",
            party=party,
            chamber=self.chamber,
            district=district,
        )

        p.add_source(self.source.url)
        p.add_source(detail_link)
        p.add_link(detail_link, note="homepage")

        return LegDetail(p, source=detail_link)


class House(LegList):
    source = "https://ilga.gov/house/default.asp?GA=102"
    chamber = "lower"


class Senate(LegList):
    source = "https://ilga.gov/senate/default.asp?GA=102"
    chamber = "upper"
