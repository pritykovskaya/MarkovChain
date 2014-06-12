# -*- coding: utf-8 -*-
from collections import Counter
from random import *
from optparse import *
from format_html import create_paragraph_files


def mean(vector):
    return sum(vector) * 1.0 / len(vector)

def sum_all_values(dict):
    return float(sum(dict.values()))


def read_source_file(file_path):
    with open(file_path, "r") as file_:
        return file_.read()


def read_frequencies_from_file(filename):
    distribution = {}
    with open(filename, "r") as file_:
        lines = file_.readlines()

    for line_ in lines:
        parts = line_.strip().rsplit(" ", 1)
        distribution[parts[0]] = int(parts[1])

    return distribution


def create_empirical_distribution_function(variable_frequencies_dict):
    weight = sum_all_values(variable_frequencies_dict)
    for variable in variable_frequencies_dict.keys():
        variable_frequencies_dict[variable] /= weight
    return variable_frequencies_dict


def variable_by_distribution(variable_empirical_dist_function_dict):
    """ generate discrete variable basing on empirical distribution function"""
    probability = random()

    for variable in variable_empirical_dist_function_dict.keys():
        if probability < variable_empirical_dist_function_dict[variable]:
            return variable
        else:
            probability -= variable_empirical_dist_function_dict[variable]


def generate_discrete_random_variable_on_giving_frequencies(variable_frequencies_dict):
    variable_empirical_dist_function_dict = create_empirical_distribution_function(
        variable_frequencies_dict)
    return variable_by_distribution(
        variable_empirical_dist_function_dict)


def count_paragraph_stats(paragraph_file):
    # sentence_lengths_in_words
    sentences_lengths = []
    # paragraph_lengths_in_sentences
    paragraph_lengths = []
    paragraph = read_source_file(paragraph_file).split("\n")
    sentences_count = 0
    for line_ in paragraph:
        if line_.strip() != "END_PARAGRAPH":
            sentences_count += 1
            sentences_lengths.append(len(line_.strip().decode("utf-8").split(" ")))
        else:
            paragraph_lengths.append(sentences_count)
            sentences_count = 0

    return mean(paragraph_lengths), mean(sentences_lengths)


def count_all_paragraphs_stats(responsibilities_file, requirements_file):
    responsibilities_mean_paragraph_len, responsibilities_mean_sentence_len = \
        count_paragraph_stats(responsibilities_file)

    requirements_mean_paragraph_len, requirements_mean_sentence_len = \
        count_paragraph_stats(requirements_file)

    return responsibilities_mean_paragraph_len, responsibilities_mean_sentence_len, \
           requirements_mean_paragraph_len, requirements_mean_sentence_len


def count_sentences_number(size, requirements_file, responsibilities_file):
    responsibilities_mean_paragraph_len, responsibilities_mean_sentence_len, \
        requirements_mean_paragraph_len, requirements_mean_sentence_len \
        = count_all_paragraphs_stats(requirements_file, responsibilities_file)

    ratio = ((responsibilities_mean_paragraph_len * responsibilities_mean_sentence_len) /
            (requirements_mean_paragraph_len * requirements_mean_sentence_len))

    requirement_words = int(size) * 1.0 / (1 + int(ratio))
    responsibilities_words = int(size) - requirement_words

    requirement_sentences = requirement_words / requirements_mean_sentence_len
    responsibilities_sentences = responsibilities_words / responsibilities_mean_sentence_len

    return requirement_sentences, responsibilities_sentences


class MarkovChainNode(object):
    """Class containing info about all MarkovChainNodes where it is possible to get from the current one."""
    def __init__(self, ngram):
        self.ngram = ngram
        self.next_states = {}

    def add_next_state(self, node, probability):
        self.next_states[node] = probability

    def get_next_state(self):
        # Randomly select a next node from the chain, giving higher
        # priority to the letters that follow this n-gram more often.

        if len(self.next_states) != 0:
            return variable_by_distribution(
                self.next_states)
        else:
            return None


def compute_ngram_counts(text, n_gram_length):
    ngrams = {}
    start_distribution = {}
    # realization of the mode, where stat counts only basing on one sentence

    sentences = text.split("\n")
    sentences = filter(lambda x: x != "END_PARAGRAPH", sentences)

    sentences_shorter_than_k_count = 0

    for sentence in sentences:
        words = sentence.split(" ")
        sentence_length = len(words)

        if sentence_length < n_gram_length:
            # Sentence is too short to extract anything useful.
            sentences_shorter_than_k_count += 1
            continue

        if words[0:n_gram_length] in start_distribution.keys():
            start_distribution[" ".join(words[0:n_gram_length])] += 1
        else:
            start_distribution[" ".join(words[0:n_gram_length])] = 1

        for i in range(0, sentence_length - n_gram_length + 1):
            ngram = " ".join(words[i: i + n_gram_length])

            # Look at the word following the n-gram and increase the count
            # associated with it. If it is the first time it is seen, the count is 1.
            if i != sentence_length - n_gram_length:
                next_word = words[i + n_gram_length]
            else:
                next_word = None

            # The words following a n-gram are stored as a dictionary of
            # (word : occurrence_count) pairs.
            if not ngram in ngrams:
                ngrams[ngram] = {}

            next_ngram_words = ngrams[ngram]

            if next_word is not None:
                if next_word in next_ngram_words:
                    next_ngram_words[next_word] += 1
                else:
                    next_ngram_words[next_word] = 1

    if sentences_shorter_than_k_count > len(sentences) / 2:
        raise Exception(
            "More than half of the sentences have less than {0} words. Reduce {1}".format(n_gram_length, n_gram_length))

    return ngrams, Counter(start_distribution)


def build_markov_chain(ngrams):
    # First build the Markov nodes for all n-grams,
    # then connect the nodes using the next-word information.
    chain_nodes = {}

    for ngram in ngrams:
        #print ngram
        chain_nodes[ngram] = MarkovChainNode(ngram)

    for ngram, next_words in ngrams.items():
        # For each word compute the probability that it follows after the n-gram.

        weight = sum_all_values(next_words)
        node = chain_nodes[ngram]

        for word, count in next_words.items():
            # The next n-gram consists of the first K-1 words
            # from the current node and the last word from the next node.

            ngram_without_first_world = " ".join(ngram.split(" ")[1:])
            next_state_ngram = " ".join([ngram_without_first_world, word]).strip()

            #print next_state_ngram
            next_state_node = chain_nodes[next_state_ngram]
            node.add_next_state(next_state_node, count / weight)

    return chain_nodes


def generate_text(chain, start_distribution, length):
    # Randomly select one of the chain nodes as the start node.
    # For the start node the entire n-gram is used, while for the next
    # states only the last word, until the required length is reached.
    node = chain[choice(start_distribution.keys())]

    text = []
    sentence = []
    text_length = 0

    for word in node.ngram.split(" "):
        sentence.append(word)

    while text_length < length:
        node = node.get_next_state()
        if node is not None:
            sentence.append(node.ngram.split(" ")[-1])
        else:
            sentence_start = choice(start_distribution.keys())
            node = chain[sentence_start]
            text_length += 1
            text.append(" ".join(sentence))
            sentence = []
            for word in node.ngram.split(" "):
                sentence.append(word)

    return text


def write_text_to_file(text, file_path):
    with open(file_path, "w") as file_:
        file_.write(text)


def generate_paragraph(file_path, ngram_length, size_in_sentences):
    text = read_source_file(file_path)
    ngrams, start_distribution = compute_ngram_counts(text, ngram_length)

    # Build the Markov chain and create the text.
    chain = build_markov_chain(ngrams)
    output_text = generate_text(chain, start_distribution, size_in_sentences)

    return output_text


def find_and_delete_first_longest_sentence_from_paragraph(paragraph):
    sentences_dict = {}
    longest_sentence_len = 0
    for sentence in paragraph:
        sentence_len = len(sentence.split(" "))
        sentences_dict[sentence] = sentence_len
        if longest_sentence_len < sentence_len:
            longest_sentence_len = sentence_len

    for sentence in sentences_dict:
        if sentences_dict[sentence] == longest_sentence_len:
            del sentences_dict[sentence]
            return list(sentences_dict.keys())


def compile_final_text(company, position, requirements_paragraph, responsibilities_paragraph,
                       size):
    output_text = "\n\n".join(
        ["Компания: " + company, "Должность: " + position,
         "Требования:\n" + '\n'.join(requirements_paragraph),
         "Обязанности:\n" + '\n'.join(responsibilities_paragraph)])

    actual_text_length = len(output_text.split())
    counter = 0

    while not size - 0.2 * size <= actual_text_length <= size + 0.2 * size:
        if counter % 2 == 0:
            responsibilities_paragraph = find_and_delete_first_longest_sentence_from_paragraph(
                responsibilities_paragraph)
        else:
            requirements_paragraph = find_and_delete_first_longest_sentence_from_paragraph(
                requirements_paragraph)
        counter += 1
        output_text = "\n\n".join(
            ["Компания: " + company, "Должность: " + position,
             "Требования:\n" + '\n'.join(requirements_paragraph),
             "Обязанности:\n" + '\n'.join(responsibilities_paragraph)])

        actual_text_length = len(output_text.split())

    return output_text


def main():
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="path",
                      help="The path to file with text to learn on.")
    parser.add_option("-d", "--depth", dest="depth",
                      help="The length of the used n-gram (in words).")
    parser.add_option("-s", "--size", dest="size",
                      help="The number of words the output text should contain.")
    parser.add_option("-o", "--out", dest="output",
                      help="The file where the output text should be written.")
    options, args = parser.parse_args()

    if options.size is None:
        print("Size of output text not specified!")
        return -1

    if options.output is None:
        print("Path to output text not specified!")
        return -1

    if options.depth is None:
        print("Length of used n-gram not specified!")
        return -1

    if options.path is not None:
        print("Generating {0} words from source files {1}".format(options.size,
                                                                  options.path))
        ngram_length = int(options.depth)
        companies_file, positions_file, requirements_file, responsibilities_file = \
            create_paragraph_files(options.path)
        requirements_sentences_numb, responsibilities_sentences_numb = count_sentences_number(
            options.size, responsibilities_file, requirements_file)
        requirements_paragraph = generate_paragraph(requirements_file, ngram_length,
                                                    requirements_sentences_numb - 1)
        responsibilities_paragraph = generate_paragraph(responsibilities_file, ngram_length,
                                                        responsibilities_sentences_numb - 1)

    elif options.responsibilities is None:
        print("Path to responsibilities text file not specified!")
        return -1
    elif options.requirements is None:
        print("Path to requirements text file not specified!")
        return -1

    position_dist = read_frequencies_from_file(positions_file)
    position = generate_discrete_random_variable_on_giving_frequencies(position_dist)

    company_dist = read_frequencies_from_file(companies_file)
    company = generate_discrete_random_variable_on_giving_frequencies(company_dist)

    output_text = compile_final_text(company, position, requirements_paragraph,
                                     responsibilities_paragraph, int(options.size))

    write_text_to_file(output_text, options.output)

if __name__ == '__main__':
    main()
