import codecs
import os
import re
from datetime import date

SUCCESS_FOLDER = "DecidingForceArticles"
ARTICLE_FOLDER = "DecidingForceErrors"
ERROR_FOLDER = "DecidingForceErrors_v2"
#ARTICLE_FOLDER = "DecidingForceArticles_Sample/"

# Format of the article filenames.
# Example: 1000BethlehemPA-LehighValleyLive-02.txt
FILENAME_RE = (r'^(?P<article_id>\d+)' # article ID
               '-?' # optional hyphen
               '(?P<city>[\w\ -]+)' # city name
               ',? ?' # optional space and comma
               '(?P<state>[A-Z][A-Z])?' # optional state name
               '-' # hyphen
               '(?P<periodical>[\w\.]+)' # periodical name
               '-' # hypen
               '\s*' # optional whitespace
               '(?P<periodical_code>\d+)' # periodical code
               '\.txt' # extension
           )

# Format of a TUA tag.
# Example: <2><Camp>using social networking, emails/></>
TUA_RE = (r'(<(?P<tua_id>\d+)>)?' # optional id number (<2>)
          '<(?P<tua_type>[^>]+)>' # the type (<Protester>)
          '(?P<tua_body>.+?)' # the body (...text...)
          '/>(</>)?' # the close tags
)

# Format of some text inside of brackets.
# Example: [<2><Camp>Some text] goes here/></>
BRACKET_RE = (r'\[' # open bracket
              '(<[^>]*>)*' # possible TUA start tags
              '(?P<text>[^\]/<>]*)' # the actual text
              '(/>(</>)?)?' # possible TUA end tags
              '\]' # close bracket
          )

# Format of the date published header line. Example: 11-5-11
DATE_HEADER_RE = r'(?P<month>\d+)-(?P<day>\d+)-(?P<year>\d+)'

# Format of an annotator. Example: <!!>SLG</>
ANNO_RE = r'(<!!>)?\s*(?P<annotator>[A-Z]+)\s*(</>)?'

# Format of the version. Example: v23
VERSION_RE = r'v(?P<version>\d+)'

def parse_document(path):
    with open(path, 'r') as f:
        raw_text = f.read()

    # extract info from the file name
    article_id, city, state, periodical, periodical_code = parse_filename(path)

    # extract info from the header and remove it from the text
    (clean_text, date_published, annotators, version) = parse_header(raw_text)

    # store type and offset information for each TUA, and strip TUA tags from
    # the text
    tuas = {}
    raw_tuas, clean_text = parse_and_clean_tuas(clean_text)
    for tua_id, tua_type, tua_body, tua_span in raw_tuas:
        if tua_type not in tuas:
            tuas[tua_type] = {}
        if tua_id not in tuas[tua_type]:
            tuas[tua_type][tua_id] = []
        assert (clean_text[tua_span[0]:tua_span[1]].strip().lower()
                == tua_body.strip().lower())
        tuas[tua_type][tua_id].append(tua_span)

    # print out our data.
    # TODO: store this somewhere.
    print "final clean text:", clean_text
    import pprint; pprint.pprint(tuas)
    print "annotators:", annotators
    print "version:", version
    print "date published:", date_published
    print "article ID:", article_id
    print "city:", city
    print "state:", state
    print "periodical:", periodical
    print "periodical code:", periodical_code
    print "\n\n\n"

def parse_header(raw_text):
    # expected header format:
    #
    # A 3-line paragraph containing:
    #   +*+*      <-- special separator text
    #   11-5-11   <-- Date published (month-day-year)
    #   <!!>SLG</>, v23  <-- annotators and version number
    lines = raw_text.splitlines()
    header_rownum = 1
    for i, line in enumerate(lines):
        # Remove windows UTF-8 junk
        if line.startswith(codecs.BOM_UTF8):
            line = line[3:]

        # Skip blank lines
        if not line.strip():
            continue

        # Start of Header
        if line.strip() == '+*+*':
            header_rownum = 2

        # Unknown line
        elif header_rownum == 2:
            date_published = parse_date_line(line)
            header_rownum = 3

        # Annotator / Version line
        elif header_rownum == 3:
            annotators, version = parse_annotator_line(line)
            if not annotators and not version:
                raise ValueError('Unexpected header line 3: ' + line)
            break

    headerless_text = '\n'.join(lines[i+1:]).strip()
    return (headerless_text, date_published, annotators, version)

def parse_date_line(raw_text):
    # Format: month-day-year
    # Example: 11-8-11
    match = re.search(DATE_HEADER_RE, raw_text)
    date_published = None
    if match:
        month, day, year = match.group('month', 'day', 'year')
        date_published = date(2000 + int(year), int(month), int(day))
    elif 'Undated' not in raw_text:
        raise ValueError('Unexpected header line 2: ' + line)

    return date_published

def parse_annotator_line(raw_text):
    # Format: <!!>ABC</>, v##[, <!!>BCD</>]
    # Examples:
    #   <!!>SLG</>, v23
    #   <!!>CRV</>, v26, <!!> EDC</>
    annotators = []
    version = None
    for anno_match in re.finditer(ANNO_RE, raw_text):
        annotators.append(anno_match.group('annotator'))
    version_match = re.search(VERSION_RE, raw_text)
    if version_match:
        version = version_match.group('version')
    return (annotators, version)

def parse_and_clean_tuas(raw_text):
    # Extract metadata about TUAs and clean their tags out of the text.
    # See TUA_RE above for TUA formatting.

    tuas = []
    tuas_to_finalize = []
    match = re.search(TUA_RE, raw_text)
    while match:
        t_id, t_type, t_body = match.group('tua_id', 'tua_type', 'tua_body')
        t_id = 1 if t_id is None else t_id

        # Brackets represent back-references to previous text. We need to
        # create TUAs to capture the references to the previous text, then
        # remove the bracketed text from the article.
        has_brackets, clean_text, new_tuas = extract_bracket_text(match, raw_text)
        if has_brackets:
            raw_text = clean_text
            for new_tua_body, new_tua_index in new_tuas:
                if new_tua_index == 0: # forward reference--we need to wait.
                    tuas_to_finalize.append((t_id, t_type, new_tua_body,
                                             new_tua_index))
                else:
                    t_span = get_match_span_by_index(
                        re.escape(new_tua_body.strip()),
                        new_tua_index, raw_text)
                    tuas.append((t_id, t_type, new_tua_body, t_span))
        else: # No brackets to remove, just parse and clean the TUA.
            t_start = match.start('tua_body')
            t_index = find_match_index(re.escape(t_body), t_start, raw_text)
            raw_text = merge_with_spacing((raw_text[:match.start()],
                                          t_body,
                                           raw_text[match.end():]))
            t_span = get_match_span_by_index(re.escape(t_body.strip()), t_index,
                                             raw_text)
            tuas.append((t_id, t_type, t_body, t_span))
        match = re.search(TUA_RE, raw_text)

    for t_id, t_type, t_body, t_index in tuas_to_finalize:
        t_span = get_match_span_by_index(re.escape(t_body.strip()), t_index,
                                         raw_text)
        tuas.append((t_id, t_type, t_body, t_span))

    return (tuas, raw_text)

def find_match_index(regex, match_start, source_text):
    # if regex matches multiple times in source_text, return the index of the
    # match that begins at offset match_start.
    # Returns None if there is no such match
    match_index = None
    for match_num, match in enumerate(re.finditer(regex, source_text, re.I)):
        if match.start() == match_start:
            match_index = match_num
            break
    return match_index

def get_match_span_by_index(regex, match_index, source_text):
    # Return the index into source_text where regex matches the text for the
    # match_index'th time.
    for match_num, match in enumerate(re.finditer(regex, source_text, re.I)):
        if match_num == match_index:
            return match.span()
    raise ValueError("Match doesn't occur correct number of times")

def extract_bracket_text(match, source_text):
    # brackets might be anywhere starting from the character before the match to
    # the character after it.
    m_start, m_end = match.span()
    bracket_area = source_text[m_start-1:m_end+1]
    if '[' not in bracket_area[:-1] and ']' not in bracket_area[1:]:
        return (False, '', [])

    body_start, body_end = match.span('tua_body')
    try:
        cut_start = m_start if source_text[m_start-1] != '[' else m_start - 1
    except IndexError:
        cut_start = 0

    try:
        cut_end = m_end if source_text[m_end] != ']' else m_end + 1
    except IndexError:
        cut_end = m_end

    bits_to_keep = []
    keep_start_index = body_start
    tuas_to_create = []
    for bracket in re.finditer(BRACKET_RE, source_text[m_start-1:m_end+1]):
        # Find the backreference in the article text and set up a new TUA.
        bracket_text = bracket.group('text')
        if bracket_text == 'DT': # special case--this is never a true bracket.
            continue
        bracket_text_index = find_match_index(
            re.escape(bracket_text),
            m_start - 1 + bracket.start('text'),
            source_text)
        # at least one occurrence before the bracket--back reference.
        if bracket_text_index != 0:
            bracket_text_index -= 1
        tuas_to_create.append((bracket_text, bracket_text_index))

        # Track the text we need to remove
        # The bracket match is relative to the TUA match, so ajdust the offset.
        bracket_start = bracket.start() + m_start - 1
        bracket_end = bracket.end() + m_start - 1
        bits_to_keep.append((keep_start_index,
                             max(bracket_start, body_start)))
        keep_start_index = min(bracket_end, body_end)

    # reassemble the bracket-less text that needs to stay in the article
    bits_to_keep.append((keep_start_index, body_end))
    remaining_body = merge_with_spacing([source_text[span[0]:span[1]]
                                         for span in bits_to_keep])
    clean_text = merge_with_spacing((source_text[:cut_start],
                                     remaining_body,
                                     source_text[cut_end:]))
    return (True, clean_text, tuas_to_create)

def merge_with_spacing(string_bits):
    # Merge the strings in string_bits with exactly n_spaces spaces between them
    separator = ' '
    no_emptys = [bit for bit in string_bits if bit.strip(' ')]
    if not no_emptys:
        return ''
    return join_safe(separator, no_emptys)

def join_safe(separator, bits_to_join):
    def merge_safe(a, b):
        if not a:
            return b
        if not b:
            return a

        if requires_separator(a, b):
            return a.rstrip(separator) + separator + b.lstrip(separator)
        else:
            return a.rstrip(separator) + b.lstrip(separator)


    return reduce(merge_safe, bits_to_join, '')

def requires_separator(a, b):
    no_separator_chars_left = ['\n', '\x9c']
    no_separator_chars_right = ['\n', ',', '.',]
    no_separator_pair_right = ['"\n', '" ']
    return (a[-1] not in no_separator_chars_left
            and b[0] not in no_separator_chars_right
            and b[0:2] not in no_separator_pair_right)

def parse_filename(filename):
    # Extract metadata from the filename. See FILENAME_RE for formatting info.
    raw_name = os.path.basename(filename)
    match = re.search(FILENAME_RE, raw_name)
    if match:
        return match.group('article_id', 'city', 'state', 'periodical',
                           'periodical_code')
    else:
        raise ValueError('bad file name: ' + raw_name)

def parse_documents(directory_path, error_directory_path):
    for file_path in os.listdir(directory_path):
        print "PROCCESING FILE:", file_path, "..."
        full_path = os.path.join(directory_path, file_path)
        try:
            parse_document(full_path)
        except Exception:
            raise
            os.rename(full_path, os.path.join(error_directory_path, file_path))
            print "ERROR!"

if __name__ == '__main__':
    parse_documents(ARTICLE_FOLDER, ERROR_FOLDER)
