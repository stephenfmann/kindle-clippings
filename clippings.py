"""
    clippings.py
    Take a Kindle clippings .txt file and convert to JSON; output as .json file
"""

import re, json, sys, io
from time import strptime
from datetime import datetime


DUMMY_AUTHOR = "ZZNOAUTHOR" # Quotes with no author will be assigned this name

def do_clippings():
    """
        Wrapper
    """
    
    if len(sys.argv) > 1:
        f_in = sys.argv[1]          # clippings filename (should be .txt)
        if len(sys.argv) > 2:
            f_out = sys.argv[2]     # output filename (should be .json)
        else:
            f_out="out/clippings.json"
    else:
        f_in = "in/My Clippings.txt"    # default
        f_out="out/clippings.json"       # default
    
    print("Extracting clippings from "+f_in)
    
    with open(f_in,"r",encoding='utf-8') as f:
        raw = f.read()
    
    dict_all = parse_raw(raw)
    
    output(dict_all,f_out)


def parse_raw(raw):
    """
        Convert Kindle clippings text file to JSON and print to JSON file
    """
    
    ## 1. Preprocessing e.g. byte order mark
    raw = preprocess(raw)
    
    ## 2. Get regular expressions
    regex_author_str, regex_noauthor_str = build_regexes()
    
    ## 3. Perform the regex for entries with an author
    regex_author = re.compile(regex_author_str)
    dict_author = {"notes_author":regex_author.findall(raw)}
    
    ## 4. Perform the regex for entries without an author
    regex_noauthor = re.compile(regex_noauthor_str)
    dict_noauthor = {"notes_noauthor":regex_noauthor.findall(raw)}
    
    ## 5. Create the dictionary
    dict_all = dict_author
    dict_all.update(dict_noauthor)
    
    ## 6. Organise the dictionary
    dict_all = organise(dict_all)
    
    return dict_all


def preprocess(raw):
    """
        Basic text formatting e.g. BOM at start of file
    """
    
    
    ## 1. Remove byte order marks if necessary
    
    if raw[0]=='\ufeff':
        raw = raw[1:]
    
    # if raw[0] == '\xef':
        # raw = raw[1:]

    # if raw[0] == '\xbb':
        # raw = raw[1:]

    # if raw[0] == '\xbf':
        # raw = raw[1:]
    
    return raw


def build_regexes():
    """
        Create regular expressions to extract quote data.
    """
    
    
    ## 1. Regex parts
    title_regex = "(.+)"
    title_author_regex = "(.+) \((.+)\)"
    
    ## 2. Regex locations
    loc_all_regex = "(Loc.|on Page) ([0-9]+)( |-([0-9]+)  )"
    
    ## 3. Regex date and time
    date_regex = "([a-zA-Z]+), ([a-zA-Z]+) ([0-9]+), ([0-9]+)"  # Date
    time_regex = "([0-9]+):([0-9]+) (AM|PM)"  # Time
    
    ## 4. Regex quote
    content_regex = "(.*)"
    footer_regex = "=+"
    
    ## 5. Regex newline
    nl_re = "\n*"
    
    ## 6. Regex quotes with an author
    regex_author_str =\
    title_author_regex + nl_re +\
    "- Highlight " + loc_all_regex + "\| Added on " +\
    date_regex + ", " + time_regex + nl_re +\
    content_regex + nl_re +\
    footer_regex
    
    ## 7. Regex quotes with no author
    regex_noauthor_str =\
    title_regex + nl_re +\
    "- Highlight " + loc_all_regex + "\| Added on " +\
    date_regex + ", " + time_regex + nl_re +\
    content_regex + nl_re +\
    footer_regex
    
    return regex_author_str,regex_noauthor_str


def output(dict_all,f_out=None):
    """
        Print or file write
    """
    if f_out:
        with io.open(f_out,"w",encoding='utf-8') as f:
            f.write(json.dumps(dict_all, indent=4, sort_keys=True)) # convert dictionary to string and output
            
        print("Output JSON to "+f_out)
        return
    
    print(json_string)


def organise(dict):
    """
        How do you want your JSON output organised?
        The input looks like this:
            {
                notes_noauthor:     [
                    [   <title>,
                        Loc.|on Page,
                        <loc or page>,
                        <??>,
                        <??>,
                        <day name>,
                        <month name>,
                        <day number>,
                        <year>,
                        <hour>,
                        <minute>,
                        AM/PM,
                        <quote>
                    ],
                    [...],[...]
                ],
                notes_author:       [
                    [   <title>,
                        <author>,
                        Loc.|on Page,
                        <loc or page>,
                        <??>,
                        <??>,
                        <day name>,
                        <month name>,
                        <day number>,
                        <year>,
                        <hour>,
                        <minute>,
                        AM/PM,
                        <quote>
                    ],
                    [...],[...]
                ]
            }
        I want something like this:
            {
                notes_author:   {
                    "Kate Chopin": {
                        "The Awakening and Selected Short Stories": {
                            "l1197": [
                                {
                                    "date": "20180405-1257",
                                    "quote": "She had reached a stage when she seemed to be no longer feeling her way, working, when in the humor, with sureness and ease. And being devoid of ambition, and striving not toward accomplishment, she drew satisfaction from the work in itself."
                                }
                            ]
                        }
                    }
                }
            }
    """
    
    dict_new = {"notes_author":{},"notes_noauthor":{}}
    
    ## 1. Quotes with an author
    for line in dict["notes_author"]:
        
        dict_line = build_dict_line(line)
        
        dict_new = add_line_to_dict_deep(dict_new,dict_line)
    
    ## 2. Quotes with no author
    ## TODO
    for line in dict["notes_noauthor"]:
        line2 = (line[0],DUMMY_AUTHOR)+line[1:]
        dict_line = build_dict_line(line2)
        
        dict_new = add_line_to_dict_deep(dict_new,dict_line)
    
    return dict_new


def build_dict_line(line):
    """
        Convert the line to the new format.
        The current order is:
            0 <title>,
            1 <author>,
            2 "Loc." or "on Page",
            3 <loc> or <page>,
            4 <??>,
            5 <??>,
            6 <day>,
            7 <month>,
            8 <date>,
            9 <year>,
            10 <hour>,
            11 <minute>,
            12 "AM" or "PM",
            13 <quote>
        New format:
            {
                "Ursula K. Le Guin":  {
                    "Tales from Earthsea":   {
                        "l1321": [
                            {
                                "date": "20170618-1726",
                                "quote": "The wizard kept the name Roke in his memory, and when he heard it again, and in the same connection, he knew Hound had been on a true track again."
                            }
                        ],
                    }
                }
            }
    """
    
    ## 1. Timestamp
    # # line[9] 
    # # line[7] 
    # # line[8] 
    # # line[10] 
    # # line[11] # minute
    # # line[12] # AM/PM
    year = int(line[9])                             # year
    month = int(strptime(line[7][:3],'%b').tm_mon)  # month (in words)
    day = int(line[8])                              # day
    hour = int(line[10])                            # hour
    if line[12] == "PM":                            # fix for 24 hour clock
        hour = (hour + 12) % 24
    minute = int(line[11])                          # minute
    date = datetime(year,month,day,hour,minute)     # full date
    
    ## 2. Author format
    author = line[1]
    author = author.replace('\\','') # Remove backslashes
    
    ## 3. Page/location format
    if line[2] == "on Page":
        loc = "p"
    elif line[2] == "Loc.":
        loc = "l"
    else:
        loc = ""
    
    loc = loc + str(line[3]) # combine location prefix with location.
    
    ## 4. Quote formatting
    ## TODO - lots of weird unicode stuff e.g. \u2014
    quote = line[13].replace('"','\\"')
    
    
    ## 5. Build line.
    dict_line = {
        author:{
            line[0]:{ # title
                loc:[
                    {"quote":quote,"date":date.strftime("%Y%m%d-%H%M")}
                ]
            }
        }
    }
    
    return dict_line


def add_line_to_dict_deep(dict,line):
    """
        The dict looks like:
            "notes_author": {
                "John Updike": {
                    "Rabbit, Run": {
                        "l4467": [{
                                "date": "TODO",
                                "quote": "Two thoughts comfort him, let a little light through the dense pack of impossible alternatives. Ruth has parents, and she will let his baby live: two thoughts that are perhaps the same thought, the vertical order of parenthood, a kind of thin tube upright in time in which our solitude is somewhat diluted."
                            }
                        ]
                    }
                },
            ...
            }
        So we need to check the title and location to make sure it's not overwritten.
    """
    
    ## 1. Initialise
    author      = list(line.keys())[0]
    title       = list(line[author].keys())[0]
    location    = list(line[author][title].keys())[0]
    
    
    if author not in dict["notes_author"]:
        ## 2. Author not yet added.
        dict["notes_author"].update(line)
        return dict
    
    if title not in dict["notes_author"][author]:
        ## 3. Title not yet added.
        dict["notes_author"][author].update(line[author])
        return dict
        
    if location not in dict["notes_author"][author][title]:
        ## 4. Location not yet added. 
        dict["notes_author"][author][title].update(line[author][title])
        return dict
    
    ## 5. The location is already there (should be impossible for Locs, rare for Pages)
    ## Just need to add the entry
    dict["notes_author"][author][title][location] += line[author][title][location]
    return dict


if __name__ == "__main__":
    do_clippings()