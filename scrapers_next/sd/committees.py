from spatula import JsonListPage, JsonPage, URL
from openstates.models import ScrapeCommittee


class CommitteeList(JsonListPage):

    source_string = "https://sdlegislature.gov/api/SessionCommittees/Session/68"
    source = URL(source_string)

    # I don't know if there's a method on the base class for this to be overridden
    def standardize_chamber(self, original_chamber_text):
        chamber_conversion = { "H":"lower", "S":"upper", "J":"legislature" }
        return chamber_conversion[original_chamber_text] 

    def process_item(self, item):
        committee_json = item["Committee"]

        # The Full House & Senate are included in the committe json list, tagged with the following property
        if committee_json["FullBody"]:
            self.skip(f"Not a committee: {committee_json['Name']}")

        com_id = item["SessionCommitteeId"]
        detail_link = f"https://sdlegislature.gov/api/SessionCommittees/Detail/{com_id}"
        homepage = f"https://sdlegislature.gov/Session/Committee/{com_id}/Detail"

        chamber = self.standardize_chamber(committee_json["Body"])
        if chamber is None:
            self.skip("Committee type not recognized")

        com = ScrapeCommittee(
            name=committee_json["Name"],
            chamber=chamber
        )

        com.add_source(self.source_string)
        com.add_source(detail_link)
        com.add_link(homepage, note="homepage")

        return CommitteeDetail(com, source=URL(detail_link))


class CommitteeDetail(JsonPage):
    sample_source = URL("https://sdlegislature.gov/api/SessionCommittees/Detail/1156")

    def process_page(self):
        com = self.input

        members = self.data["CommitteeMembers"]

        if members & isinstance(members, list):
            for member in members:
                member_obj = member["Member"]
                name = member_obj["FirstName"] + " " + member_obj["LastName"]
                role = member["CommitteeMemberType"]
                com.add_member(name, role)
        else:
            self.skip("Malformed committee member data")

        return com
