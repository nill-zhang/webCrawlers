# by sfzhang 2017.1.25
from scrapy.item import Item, Field
from scrapy.http import FormRequest
from scrapy.spiders import Spider
import scrapy
import re
import sys
from urllib.parse import urljoin

id_mapping = {"boston": "15160418",
              "new york": "472161106",
              "toronto": "1287161016",
              "london": "16160424",
              "chicago": "67161009"}


class MarathonSpider(Spider):
    name = "marathon"
    allowed_domains = ["marathonguide.com"]

    def start_requests(self):
        base_url = "http://www.marathonguide.com/results/browse.cfm?MIDD="
        tag = getattr(self, "tag", "notag").lower().split()
        try:
            urls = [base_url + id_mapping[i] for i in tag]
        except KeyError:
            urls = [""]

        for url in urls:
            url = urljoin(base_url, url.replace(".."))
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        year_urls = response.xpath(
            "//b[contains(text(),'Marathon Results') \
            and string-length(text()) >20]/following-sibling::a/@href") \
            .extract()
        for url in year_urls:
            yield scrapy.Request(url=url, callback=self.parse_one_year)

    def parse_one_year(self, response):
        """parse one specific year and yield all the section pages result"""
        # sections = response.css("form")[0].css("select")[0].css("option::attr(value)")[1:].extract()
        sections = response.xpath("//form/select/option/@value").extract()[1:]
        for section in sections:
            form_data = {'RaceRange': section}
            yield FormRequest.from_response(response,
                                            formnumber=0,
                                            formdata=form_data,
                                            callback=self.parse_one_section)


    def parse_one_section(self, response):
        """parse one section and yield entries in that section"""
        # if not self.has_header:
        #     csv_header = list(map(lambda x: re.sub(r"<.+?>", "", x).strip(), response.css("th").extract()))
        #     self.has_header = True
        #     yield dict(enumerate(csv_header))
        # raw_entries = response.css("table")[5].css("tr")[7:]
        # for entry in raw_entries:
        #     yield dict(enumerate(entry.css("td::text").extract()))
        column_name = map(lambda x: re.sub(r"<.+?>", "", x).strip(), response.css("th").extract())
        raw_entries = response.xpath("//tr[th]/following-sibling::tr")
        for entry in raw_entries:
            yield dict(zip(column_name, entry.xpath("td/text()").extract()))
