# -*- coding: utf-8 -*-
__author__ = 'pritykovskaya'

import random
from urllib import quote
from urllib2 import urlopen
from HTMLParser import HTMLParser


def receive_text(url):
    """Download html."""
    conn = urlopen(url)
    data = conn.read()
    html = data.decode('utf-8')
    conn.close()
    return html


class Vacancy:
    def __init__(self):
        pass

class MainTextParser(HTMLParser):
    """Class, which parsing vacancies texts."""

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_vacancy_text_block = False
        self.vacancy_title = False
        self.company_name = False
        self.text = ""
        self.p_tag = 0
        self.em_tag = 0
        self.strong_tag = 0
        self.ul_tag = 0
        self.li_tag = 0
        self.data = ""
        self.sep = "\n"

        # spike, 'cos HTMLParser doesn't parse these symbols [", &, <<, >>] correctly
        self.current_data_handling_tag_id = 0
        self.uniq_tag_id = 0


    def handle_starttag(self, tag, attrs):
        self.uniq_tag_id = random.random()
        self.current_data_handling_tag_id = 0

        if tag == 'div' and any([(k, v) == ('class', 'l-paddings b-vacancy-desc g-user-content')
                                 for k, v in attrs]):
            self.in_vacancy_text_block = True


        if tag == 'h1' and any([(k, v) == ('class', 'title b-vacancy-title')
                                for k, v in attrs]):
            self.vacancy_title = True

        if tag == 'div' and \
                (any([(k, v) == ('class', 'companyname') or (k, v) == (
                    'class', 'hht-vacancy-company') for k, v in attrs])):
            self.company_name = True

        if tag == 'p' and self.in_vacancy_text_block:
            self.p_tag += 1

        if tag == 'em' and self.in_vacancy_text_block:
            self.em_tag += 1

        if tag == 'strong' and self.in_vacancy_text_block:
            self.strong_tag += 1

        if tag == 'ul' and self.in_vacancy_text_block:
            self.ul_tag += 1

        if tag == 'li' and self.in_vacancy_text_block:
            self.li_tag += 1

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_vacancy_text_block:
            self.in_vacancy_text_block = False

        if tag == 'div' and self.company_name:
            self.company_name = False

        if tag == 'h1' and self.vacancy_title:
            self.vacancy_title = False

        if tag == 'p' and self.in_vacancy_text_block:
            self.p_tag -= 1

        if tag == 'em' and self.in_vacancy_text_block:
            self.em_tag -= 1

        if tag == 'strong' and self.in_vacancy_text_block:
            self.strong_tag -= 1

        if tag == 'ul' and self.in_vacancy_text_block:
            self.ul_tag -= 1

        if tag == 'li' and self.in_vacancy_text_block:
            self.li_tag -= 1

    def handle_data(self, data):
        if self.current_data_handling_tag_id == 0:
            self.current_data_handling_tag_id = self.uniq_tag_id
            self.sep = "\n"
        elif self.current_data_handling_tag_id == self.uniq_tag_id:
            self.sep = ""

        if self.company_name:
            if self.sep != "":
                self.data = self.sep.join([self.data, u"\nHEADER Компания:", "POINT " + data])
            else:
                self.data = self.sep.join([self.data, data])

        if self.vacancy_title:
            if self.sep != "":
                self.data = self.sep.join([self.data, u"HEADER Должность:", "POINT " + data])
            else:
                self.data = self.sep.join([self.data, data])

        if self.in_vacancy_text_block and self.p_tag and data[len(data) - 1: len(data)] == ":":
            self.data = self.sep.join([self.data, "\nHEADER " + data])

        if self.in_vacancy_text_block and self.ul_tag and self.li_tag:
            if self.sep != "":
                self.data = self.sep.join([self.data, "POINT " + data])
            else:
                self.data = self.sep.join([self.data, data])


class UrlsListParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and any([(k, v) == ('class', 'b-vacancy-list-link b-marker-link')
                               for k, v in attrs]):
            for attr in attrs:
                if attr[0] == u"href":
                    self.links.append(attr[1])

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass


def collect_urls(html):
    """Parse html and collect urls"""
    parser = UrlsListParser()
    parser.feed(html)
    return parser.links


def parse_text(html):
    """Parse html and collect text"""
    parser = MainTextParser()
    parser.feed(html)
    return parser.data


if __name__ == "__main__":

    failed_links = []

    for page in xrange(0, 100):
        start_url = "http://hh.ru/search/vacancy?text=" + quote(u"Аналитик".encode('utf-8')) + \
                    "&page=" + str(page)

        html = receive_text(start_url)
        links = collect_urls(html)
        print page

        for link in links:
            try:
                if not "career" in link:
                    link = "http://hh.ru" + link[0:link.rfind("?")]
                else:
                    link = "http:" + link[0:link.rfind("?")]
                html = receive_text(link)
                parsed_html = parse_text(html)

                with open("vacancy.txt", "a") as output:
                    output.write('\n'.join([parsed_html,
                                            "--VACANCY_END--\n"]).encode('utf-8'))
            except:
                failed_links.append(link)

    with open("failed_links.txt", "a") as output:
        output.write('\n'.join(failed_links).encode('utf-8'))
