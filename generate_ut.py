# -*- coding: utf-8 -*-
__author__ = 'pritykovskaya'

import unittest
from generate import count_sentences_number, generate_paragraph, read_frequencies_from_file, \
    generate_discrete_random_variable_on_giving_frequencies, compile_final_text


class MarkovChainTest(unittest.TestCase):
    def test_generated_text_size_limits(self):
        generated_text_size_theoretical = 100
        requirements_sentences_numb, responsibilities_sentences_numb = count_sentences_number(
            generated_text_size_theoretical, "responsibilities.txt", "requirements.txt")
        requirements_paragraph = generate_paragraph("requirements.txt", 4,
                                                    requirements_sentences_numb - 1)
        responsibilities_paragraph = generate_paragraph("requirements.txt", 4,
                                                        responsibilities_sentences_numb - 1)

        position_dist = read_frequencies_from_file("positions.txt")
        position = generate_discrete_random_variable_on_giving_frequencies(position_dist)

        company_dist = read_frequencies_from_file("companies.txt")
        company = generate_discrete_random_variable_on_giving_frequencies(company_dist)

        output_text = compile_final_text(company, position, requirements_paragraph,
                                         responsibilities_paragraph,
                                         generated_text_size_theoretical)

        generated_text_size_practical = len(output_text.split())

        lower_bound = generated_text_size_theoretical - 0.2 * generated_text_size_theoretical
        upper_bound = generated_text_size_theoretical + 0.2 * generated_text_size_theoretical

        print generated_text_size_theoretical
        print generated_text_size_practical

        success_to_meet_limit = lower_bound <= generated_text_size_practical <= upper_bound

        self.assertEqual(success_to_meet_limit, True)


if __name__ == "__main__":
    unittest.main()

