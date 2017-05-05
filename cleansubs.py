"""Read a stream of subtitles and return sentences."""

import re

class Sentencer:
    """ Split subtitles into sentences.

    First we have to deduplicate the subtitles as much as possible.
    Then we have to turn them into sentences.

    Subtitles have their own oddities (see test cases).
    """

    def __init__(self, handler):
        self.handler = handler
        self.buff = []
        self.keep_buffer = False

    def buffer(self, line):
        if line:
            self.buff.append(line)

    def clean_up(self, line):
        """Clean up a line of subtitles before it is processed.

        - Deal with places where '.' doesn't mean the end of a sentence.
        - Remove things like 'APPLAUSE' which are not dialogue.

        Potential pitfall of this: what if we have something like 'Henry
        works for Smith & Co. He is the accountant.' where the full stop
        after 'Co' is intended as a sentence end marker, *not* to denote the
        abbreviation. Unlikely but possible.
        """
        # Replace full stops that aren't the end of a sentence with <stop>
        # so they are ignored later when the text is split into sentences
        dot_after = "(Mr|Mrs|Ms|Dr|St|Inc|Ltd|Jr|Sr|Co|Rt|Hon)"
        line = re.sub(dot_after + "\.", "\\1<stop>", line)

        dot_before = "(com|co|uk|org|net|gov|io)"
        line = re.sub("\." + dot_before, "<stop>\\1", line)

        to_be_removed = "(CHEERING|AND|APPLAUSE|LAUGHTER)"
        line = re.sub(to_be_removed, "", line)

        # This captures both '. . .' and '. .', which are sometimes used
        # interchangeably, may need to be changed in the future
        ellipses = "(\.\s\.(\s\.)?)"
        line = re.sub(ellipses, "…", line)

        # Deal with decimal points
        digits = "([0-9])"
        line = re.sub(digits + "\." + digits, "\\1<stop>\\2", line)

        return line.strip()

    def remove_from_buffer(self, string_to_remove):
        """Remove given string from the buffer, and return the new buffer."""
        self.buffer_string = self.buffer_string.replace(string_to_remove, "")
        return [self.buffer_string.strip()]

    def process(self, line, part_of_multi_word_line=False):
        """Process a line of subtitles to split the subtitles into sentences.

        Currently ignores:
        - Transitions between types of subtitles
        - Additive subtitles ('The', 'The cat', 'The cat sat'…)
        - APPLAUSE etc.
        - "Quotes"
        - Real repetition in a source ('Yes.' 'Yes.'')
        - Lots else

        Needs examples and tests for:
        - The above
        - . . . 
        - ? ! and any other sentence endings
        - Sentences with more than one end marker in them
        - Lots else
        """

        # CLEAN UP
        line = line.strip()
        if not line:
            return
        line = self.clean_up(line)

        # DEDUPLICATE
        # Single words should only be buffered if they aren't part of a line
        # that has been split up for processing
        tokencount = len(line.split())
        single_word_line = tokencount < 2

        if single_word_line and not part_of_multi_word_line:
            self.buffer(line)

        # If it's more than one, check it's not just a rollup of earlier lines
        # NB: won't handle additive subs
        # Sometimes the rollup line will be split over 2 lines, instead of all
        # being on one line.
        else:
            self.buffer_string = " ".join(self.buff)

            # There may already be a multi-word line in the buffer which
            # should be ignored when comparing with rollup lines
            single_words_in_buff = [line for line in self.buff
                                    if len(line.split()) == 1]
            multi_word_lines_in_buff = [line for line in self.buff
                                        if len(line.split()) > 1]
            if len(single_words_in_buff) > 0:
                first_single_word_in_buff = single_words_in_buff[0]
                last_single_word_in_buff = single_words_in_buff[-1]

                # Sometimes the first part of the split rollup line
                # will only be one word long.
                # If so, that line will end with a sentence end marker.
                if first_single_word_in_buff == last_single_word_in_buff\
                    and first_single_word_in_buff[-1] in ['.', '!', '?']\
                    and multi_word_lines_in_buff:
                    # If you have this situation, and the buffer looks like
                    # this: ['Devon County', 'Council.', 'Really?',
                    #        'Obviously,', 'two.', 'Council']
                    # you will want to remove 'Devon County Council.' from the
                    # buffer and output it (at the bottom).
                    full_sentence = (multi_word_lines_in_buff +
                                     [first_single_word_in_buff])
                    self.buff = self.remove_from_buffer(" ".join(full_sentence))
                    # Then remove the duplicate 'Council.' from the end
                    self.buff = self.remove_from_buffer(last_single_word_in_buff)
                    # And keep the rest 'Really? Obviously, two.' in the buffer
                    # for next time
                    self.keep_buffer = True
                    self.output(full_sentence)

            single_words_in_buff = " ".join(single_words_in_buff)

            single_words_start_with_line = single_words_in_buff.find(line) == 0
            single_words_longer_than_line = len(single_words_in_buff) > len(line)
            line_fills_single_words = len(single_words_in_buff) == len(line)

            buffer_starts_with_line = self.buffer_string.find(line) == 0
            buffer_longer_than_line = len(self.buffer_string) > len(line)
            line_fills_buffer = len(self.buffer_string) == len(line)

            # If these conditions are true that means it's the first part of
            # a split rollup line, so it's removed from the buffer to prevent
            # duplication, the rest of the buffer is preserved for
            # comparison with the next line
            if buffer_starts_with_line and buffer_longer_than_line:
                self.buff = self.remove_from_buffer(line)
                self.keep_buffer = True
                self.output([line])

            # If this is true, it's a split rollup, but part of the sentence
            # is already in the buffer before the rollup lines
            elif single_words_start_with_line and single_words_longer_than_line:
                current_line = line
                full_sentence = [line for line in self.buff
                                 if len(line.split()) > 1
                                 or line in current_line]
                full_sentence = " ".join(full_sentence)

                self.buff = self.remove_from_buffer(full_sentence)
                self.keep_buffer = True

                self.output([full_sentence])
            else:
                self.keep_buffer = False

                # If these conditions are true that means it's a full rollup
                # line so the buffer should be emptied to prevent duplication
                if buffer_starts_with_line and line_fills_buffer:
                    self.buff = []

                # If these conditions are met then it's the second part of a
                # split rollup line, whatever was in the buffer before it is
                # still needed, so only remove *this* line from the buffer
                # to prevent duplication
                elif self.buffer_string.endswith(line)\
                    and not line_fills_single_words:
                    self.buff = self.remove_from_buffer(line)

                elif self.buffer_string.endswith(line)\
                    and line_fills_single_words\
                    and not line_fills_buffer:
                    self.buff = self.remove_from_buffer(line)

                # SENTENCE SPLIT
                # If it contains sentence endmarks,
                # split and send each to be processed
                fragments = re.split('([!\.\?…])', line)

                if len(fragments) == 1:
                    self.buffer(line)
                elif fragments[-1] == '':
                    # If a line ends with an end marker, re.split makes the last
                    # element in the list an empty string, which we don't need
                    fragments.pop()

                if len(fragments) == 2:
                    self.buffer("".join(fragments))
                    self.output(self.buff)
                elif len(fragments) > 2:
                    pairs = [fragments[i:i + 2] for i in range(0, len(fragments), 2)]
                    for pair in pairs:
                        # part_of_multi_word_line is important so that if you
                        # have a line like this: 'today. Tomorrow will be worse'
                        # 'today.' won't just be put in the buffer it will be
                        # treated as the end of the previous sentence
                        self.process("".join(pair), part_of_multi_word_line=True)

    def output(self, words):
        output = " ".join(words)
        output = output.replace("<stop>", ".")
        self.handler(output)
        if not self.keep_buffer:
            self.buff = []
