import re
from dataclasses import dataclass

def dump_text(text, destination="dev/dump.txt"):
    with open(destination, 'w', encoding='utf-8') as fid:
        fid.write(text)
    print(f"DEBUG : Dumped text to {destination}")

@dataclass(frozen=True)
class SpaceInsensitiveMatch:
    start: int
    end: int
    text: str

    def span(self):
        return (self.start, self.end)

def regex_ignore_chars(pattern, text, flags=0, chars=None):
    stripped = []
    index_map = []

    if chars is None:
        chars = set(" ")

    for char in chars:
        pattern = pattern.replace(char, "")

    for i, ch in enumerate(text):
        if ch not in chars:
            stripped.append(ch)
            index_map.append(i)

    stripped = "".join(stripped)

    matches = []
    for m in re.finditer(pattern, stripped, flags):
        start, end = m.span()
        orig_start = index_map[start]
        orig_end = index_map[end - 1] + 1

        matches.append(
            SpaceInsensitiveMatch(
                start=orig_start,
                end=orig_end,
                text=text[orig_start:orig_end]
            )
        )
    return matches

def extract_text_between_tags(text, start_tag, end_tag, ignore_chars=None):
    matches_start = regex_ignore_chars(start_tag, text, chars=ignore_chars)
    matches_end = regex_ignore_chars(end_tag, text, chars=ignore_chars)

    if (not matches_start) or (not matches_end):
        raise ValueError(f"Could not find start or end tags in the text. ({matches_start}, {matches_end})")

    start_index = matches_start[0].end
    end_index = matches_end[0].start

    assert start_index < end_index, "Start tag occurs after end tag."

    return text[start_index:end_index]

def tofloat(dirty_text):
    clean_text = dirty_text.strip().replace(",", ".").replace(" ", "")
    return float(clean_text)

def reformat(dirty_text, pattern, ignored_chars=None):
    """  """

    """ Check compatibility """
    unsupported_chars = [".", "+", "*"]
    for char in unsupported_chars:
        if char in pattern.replace("\\" + char, ""):
            print("Warning (reformat) : unsupported character(s) in pattern")
            return dirty_text

    if ignored_chars is None:
        ignored_chars = set(" ")

    for char in ignored_chars:
        dirty_text = dirty_text.replace(char, "")
    
    ''' Hardcode repeating characters in pattern'''
    while True:
        match_repeat = re.compile(r"\{\d+\}").search(pattern)
        if not(match_repeat):
            break
        
        i0,i1 = match_repeat.span()
        char = pattern[i0-2:i0] if (pattern[i0 - 2] == "\\") else pattern[i0-1]
        repeats = int(match_repeat.group()[1:-1])
        pattern = pattern[:i0] + char*repeats + pattern [i1:]
    
    ''' Replace characters (construct output string one char at a time, eating away at dirty text) '''
    i = 0
    output_string = ""
    while True:
        if not(dirty_text):
            # Break when all chars have been added
            break
        char = pattern[i]
        if char in ignored_chars:
            # char is one of the ignored chars : append it to output string without modification
            output_string += char
            i += 1
        else:
            if pattern[i] == "\\":
                if pattern[i:i+1] == r"\d":
                    # char is a digit : replace it with next character in matched sequence and continue
                    output_string += dirty_text[0]
                    dirty_text = dirty_text[1:]
                    i += 2
                else:
                    # unsupported : assume no special case, append escaped character and continue
                    output_string += dirty_text[0]
                    dirty_text = dirty_text[1:]
                    i += 2
            else:
                # char is a regular character : append it to the output string and continue
                output_string += dirty_text[0]
                dirty_text = dirty_text[1:]
                i += 1

    return output_string
        
if __name__ == "__main__":
    # regex_ignore_chars : Example usage
    text = "This is  a   test string."
    pattern = r"teststring"
    matches = regex_ignore_chars(pattern, text)
    for match in matches:
        print(f"Match found from {match.start} to {match.end}: '{match.text}'")

    # reformat : Example usage
    pattern = r"REFERENCE : \d{4} "
    dirty_text = "RE FEREN  CE  : 12 34"
    print(reformat(dirty_text, pattern, [" "]))