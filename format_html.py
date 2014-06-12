# -*- coding: utf-8 -*-
from collections import Counter, OrderedDict
__author__ = 'pritykovskaya'

TEXTS_QUALITY_HANDLE = True

"""
    True - add to leaning sample only texts with all clear blocks
    False - add block to learning sample if it has position name, company name and at least
            one custom block
"""

HEADER = "HEADER"
POINT = "POINT"

HEADERS_FILE = "headers.txt"
POSITIONS_FILE = "positions.txt"
COMPANIES_FILE = "companies.txt"
REQUIREMENTS_FILE = "requirements.txt"
RESPONSIBILITIES_FILE = "responsibilities.txt"


class Paragraph(object):
    """Paragraph from vacancy description divided on header and body."""
    def __init__(self, header, sentences):
        self.header = header
        self.sentences = sentences


def format_sentence(sentence):
    sentence = sentence.decode('utf-8').strip()

    # here delete all "(" and ")"
    # print type(sentence[1:])
    # print type(sentence[0].upper())

    sentence = ''.join([sentence[0].upper(), sentence[1:]])

    if sentence[len(sentence) - 1] in (";", ",", ":"):
        if sentence[len(sentence) - 2] in (".", "!", "?"):
            sentence = sentence[:(len(sentence) - 2)]
        else:
            sentence = "".join([sentence[:len(sentence) - 1], "."])
    elif sentence[len(sentence) - 1] != ".":
        sentence += "."
    return sentence.encode('utf-8')


class Vacancy(object):
    """Class containing vacancy from hh.ru divided on paragraphs."""

    def add_paragraph(self, paragraph_header, paragraph_sentences):
        if paragraph_header != "" and len(paragraph_sentences) != 0:
            if paragraph_header == "Компания":
                self.has_company_block = True
                self.company_paragraph = Paragraph(paragraph_header, paragraph_sentences)
            elif paragraph_header == "Должность":
                self.has_position_block = True
                self.position_paragraph = Paragraph(paragraph_header, paragraph_sentences)
            else:
                self.has_custom_block = True
                self.paragraphs.append(Paragraph(paragraph_header, paragraph_sentences))


    def add_sentence_to_paragraph_sentences(self, paragraph_sentence, paragraph_sentences):
        paragraph_words = paragraph_sentence.decode('utf-8').strip().split(" ")
        paragraph_words = filter(None, paragraph_words)
        paragraph_sentence = " ".join(paragraph_words).encode('utf-8')
        if paragraph_sentence == "":
            self.has_empty_sentences = True
        else:
            paragraph_sentence = format_sentence(paragraph_sentence)
            paragraph_sentences.append(paragraph_sentence)


    def __init__(self, block_lines):
        self.position_paragraph = None
        self.company_paragraph = None

        self.paragraphs = []
        #self.has_blocks_with_empty_header = False
        self.has_empty_sentences = False
        self.has_company_block = False
        self.has_position_block = False
        self.has_custom_block = False

        paragraph_header = None
        paragraph_sentences = []

        for line_ in block_lines:
            if line_.startswith(HEADER):
                self.add_paragraph(paragraph_header, paragraph_sentences)

                paragraph_header = line_[len(HEADER) + 1: len(line_) - 1]
                paragraph_sentences = []

                #if paragraph_header == "":
                    #self.has_blocks_with_empty_header = True

            if line_.startswith(POINT) and paragraph_header != "":
                paragraph_sentence = line_[len(POINT) + 1: len(line_)]
                self.add_sentence_to_paragraph_sentences(paragraph_sentence, paragraph_sentences)


    def __str__(self):
        company = "\n".join(
            [HEADER + " " + self.company_paragraph.header, self.company_paragraph.sentences[0]])
        position = "\n".join(
            ["POSITION " + self.position_paragraph.header, self.position_paragraph.sentences[0]])

        text = "\n".join([company, position])

        for paragraph in self.paragraphs:
            header = " ".join([HEADER, paragraph.header])
            body = ""
            for sentence in paragraph.sentences:
                sentence = " ".join([POINT, sentence])
                if body != "":
                    body = "\n".join([body, sentence])
                else:
                    body = sentence
                text = '\n'.join([text, header, body])
        return text


def create_headers_file_version_for_making_paragraph_structure_with_markov_models(texts_):
    headers = []
    for text_ in texts_:
        for paragraph in text_.paragraphs:
            headers.append(paragraph.header)
        headers.append("BLOCK_END")

    with open("headers_MM.txt", "w") as headers_output:
        headers_output.write("\n".join(headers))

def create_paragraph_file_with_stats(paragraph_dict, file_name):
    paragraph_dict_sorted = OrderedDict(sorted(Counter(paragraph_dict).items(), key=lambda x: x[1]))

    with open(file_name, "w") as paragraph_output:
        for paragraph, frequency in paragraph_dict_sorted.iteritems():
            paragraph_output.write(paragraph + " " + str(frequency) + "\n")


def create_headers_file(texts):
    headers = []
    for text in texts:
        for paragraph in text.paragraphs:
            headers.append(paragraph.header)
    create_paragraph_file_with_stats(headers, HEADERS_FILE)

def create_positions_file(texts):
    positions = []
    for text in texts:
        positions.append(text.position_paragraph.sentences[0])
    create_paragraph_file_with_stats(positions, POSITIONS_FILE)


def create_companies_file(texts):
    companies = []
    for text in texts:
        companies.append(text.company_paragraph.sentences[0])
    create_paragraph_file_with_stats(companies, COMPANIES_FILE)

def create_specified_paragraph_file(texts, paragraph_name, file_name):
    parts_of_text_for_learning = []
    for text in texts:
        for paragraph in text.paragraphs:
            if paragraph_name == paragraph.header:
                parts_of_text_for_learning += ['\n'.join(paragraph.sentences), 'END_PARAGRAPH']
    with open(file_name, "w") as specified_paragraph_output:
        specified_paragraph_output.write('\n'.join(parts_of_text_for_learning))



def create_clean_vacancies_file(texts):
    with open("vacancy_clean.txt", "w") as clean_learning_file:
        clean_learning_file.write('\n--VACANCY_END--\n'.join(map(str, texts)))
        clean_learning_file.write('\n--VACANCY_END--')


def create_paragraph_files(html_file):
    with open(html_file, "r") as learning_file:
        lines = filter(None, (line.strip() for line in learning_file))

    count = 0
    texts = []
    block_lines = []
    for line in lines:
        if line.strip() != "--VACANCY_END--":
            block_lines.append(line)
        else:
            text = Vacancy(block_lines)
            if text.has_company_block and text.has_custom_block and text.has_position_block:
                texts.append(text)
            else:
                count += 1
            block_lines = []

    #print "Failed to parse: " + str(count)
    #print "Parsed: " + str(len(texts))
    #create_headers_file(texts)
    #create_headers_file_version_for_making_paragraph_structure_with_markov_models(texts)

    create_companies_file(texts)
    create_positions_file(texts)
    create_specified_paragraph_file(texts, "Требования", REQUIREMENTS_FILE)
    create_specified_paragraph_file(texts, "Обязанности", RESPONSIBILITIES_FILE)

    return COMPANIES_FILE, POSITIONS_FILE, REQUIREMENTS_FILE, RESPONSIBILITIES_FILE

if __name__ == "__main__":
    create_paragraph_files("vacancy.txt")