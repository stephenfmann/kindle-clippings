"""
    clippings.py
    Take a Kindle clippings .txt file and convert to JSON; output as .json file
"""

import re, json, sys, io, argparse
from time import strptime
from datetime import datetime


DUMMY_AUTHOR = "zznoauthor" # Lower case to ensure it goes at the end.

DEFAULT_IN = "in/My Clippings.txt"      # clippings file
DEFAULT_OUT = "out/clippings.json"      # output file
DEFAULT_SUB = "in/subs.json"            # substitute authors/titles
DEFAULT_COMBINE = "in/combine.json"     # existing quotes to combine with output

PROG_USAGE = 'python clippings.py '+\
        '[-i <input.txt>] '+\
        '[-o <output.json>] '+\
        '[-s [<substitute_file.json>]] '+\
        '[-c [<combine_file.json>]]'

def do_clippings():
    """
        Wrapper
    """
    
    ## 1. Get user input
    f_in,f_out,f_substitute,f_combine = parse_arguments()
    
    ## 2. Log
    print("Extracting clippings from "+f_in.name)
    
    ## 3. Get raw clippings
    #with open(f_in,"r",encoding='utf-8') as f:
    #    raw = f.read()
    raw = f_in.read()
    f_in.close()
    
    ## 4. Parse into dictionary
    dict_all = parse_raw(raw)
    
    ## 5. Organise the dictionary
    dict_all = organise(dict_all)
    
    ## 6. Make substitutions if necessary
    if f_substitute:
        dict_all = substitute(dict_all,f_substitute)
    
    ## 7. Combine if necessary
    if f_combine:
        dict_all = combine(dict_all,f_combine)
    
    ## 8. Output the dictionary
    output(dict_all,f_out)

def parse_arguments():
    """
        Controls how the script deals with command-line arguments.
    """
    
    parser = argparse.ArgumentParser( # See https://docs.python.org/3.7/library/argparse.html
                description='Convert Kindle clippings to JSON format.',
                usage=PROG_USAGE)
    
    parser.add_argument( 
            '-i',
            nargs='?', # expects one argument after -i
            const=DEFAULT_IN, # default if -i is provided but no file specified
            default=DEFAULT_IN, # default if -i is not provided
            help='TXT file of Kindle clippings. See README.md.',
            type=argparse.FileType('r',encoding="utf-8") # expect a filename
            )
    
    parser.add_argument( 
            '-o',
            nargs='?', # expects one argument after -o
            const=DEFAULT_OUT, # default if -o is provided but no file specified
            default=DEFAULT_OUT, # default if -o is not provided
            help='JSON file for output. See README.md for format.',
            type=argparse.FileType('w',encoding="utf-8") # expect a filename
            )
    
    parser.add_argument(
            '-s',
            nargs='?', # expects one argument after -s
            const=DEFAULT_SUB, # default if -s is provided but no file specified
            default=None, # default if -s is not provided
            help='JSON file specifying author/title substitutions. See README.md for correct format.',
            type=argparse.FileType('r',encoding="utf-8") # expect a filename
            )
    
    parser.add_argument(
            '-c',
            nargs='?', # expects one argument after -c
            const=DEFAULT_COMBINE, # default if -c is provided but no file specified
            default=None, # default if -c is not provided
            help='JSON file specifying existing quotations to combine. See README.md for correct format.',
            type=argparse.FileType('r',encoding="utf-8") # expect a filename
            )
    
    args = parser.parse_args()
    return args.i, args.o, args.s, args.c


"""
    Primary functions:
        parse_raw, organise, output
"""
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
    progress("Regex complete ",0,2)
    dict_author = {"notes_author":regex_author.findall(raw)}
    
    ## 4. Perform the regex for entries without an author
    regex_noauthor = re.compile(regex_noauthor_str)
    progress("Regex complete ",1,2)
    dict_noauthor = {"notes_noauthor":regex_noauthor.findall(raw)}
    
    ## 5. Create the dictionary
    dict_all = dict_author
    dict_all.update(dict_noauthor)
    
    return dict_all


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
    """
    
    dict_new = {}
    
    ## 1. Quotes with an author
    i=0
    total = len(dict["notes_author"]) + len(dict["notes_noauthor"])
    for line in dict["notes_author"]:
        
        dict_line = build_dict_line(line)
        
        dict_new = add_line_to_dict_deep(dict_new,dict_line)
        
        progress("Author complete: ",i,total)
        i+=1
    
    ## 2. Quotes with no author
    for line in dict["notes_noauthor"]:
        line2 = (line[0],DUMMY_AUTHOR)+line[1:]
        dict_line = build_dict_line(line2)
        
        dict_new = add_line_to_dict_deep(dict_new,dict_line)
        
        progress("No author complete: ",i,total)
        i+=1
    
    ## 3. Pad location keys.
    ##     See function comment text for explanation.
    dict_new = pad_location_keys(dict_new)
    
    return dict_new

def substitute(dict_all, f_substitute):
    """
        Substitute errant authors/titles with the correct ones.
        Subs file should be a list of objects with form:
            {
                "old":  {
                    "author":   "Batchie",
                    "title":    "Jose_Saramago_Seeing__"
                "new":  {
                    "author_new":   "José Saramago",
                    "title_new":    "Seeing"
                }
            }
    """
    
    print("Substituting features from "+f_substitute.name)

    dict_subs = json.loads(f_substitute.read())
    f_substitute.close()
    
    for entry in dict_subs:
        author = entry["old"]["author"]
        title = entry["old"]["title"]
        author_new = entry["new"]["author"]
        title_new = entry["new"]["title"]
        
        ## Create new entry
        line={author_new:{title_new:dict_all[author][title]}}
        add_line_to_dict_deep(dict_all,line)
        
        ## Delete old entry
        del dict_all[author][title]
        
        ## Delete old author if empty
        if len(dict_all[author]) < 1:
            del dict_all[author]
    
    return dict_all

def combine(dict_all, f_combine):
    """
        Combine quotes from file f_combine into dict_all.
    """
    
    ## TODO
    pass

    return dict_all

def output(dict_all,f_out=None):
    """
        Print or file write
    """
    
    if f_out:
        #with io.open(f_out,"w",encoding='utf-8') as f:
        #    f.write(
        f_out.write( 
                json.dumps(     # convert dictionary to string and output
                    dict_all,
                    indent=4,
                    sort_keys=True,
                    ensure_ascii=False  # unicode characters
                )
            ) 
            
        print("Output JSON to "+f_out.name)
        return
    
    ## Else, output to STDOUT
    print(json.dumps(dict_all))


"""
    Helper functions
"""

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
    
    ## 4. Quote
    ##  Add formatting here if necessary.
    quote = line[13]
    
    
    ## 5. Build line.
    dict_line = {
        author:{
            line[0]:{ # title
                loc:[
                    {"quote":quote,"date":date.strftime("%Y-%m-%dT%H:%M")}
                ]
            }
        }
    }
    
    return dict_line


def add_line_to_dict_deep(d,line):
    """
        The dict looks like:
            {
                "John Updike": {
                    "Rabbit, Run": {
                        "l4467": [{
                                "date": "20171011-2249",
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
    
    
    if author not in d:
        ## 2. Author not yet added.
        d.update(line)
        return d
    
    if title not in d[author]:
        ## 3. Title not yet added.
        d[author].update(line[author])
        return d
        
    if location not in d[author][title]:
        ## 4. Location not yet added. 
        d[author][title].update(line[author][title])
        return d
    
    ## 5. The location is already there (should be impossible for Locs, rare for Pages)
    ## Just need to add the entry
    d[author][title][location] += line[author][title][location]
    return d


def pad_location_keys(dict_new):
    """
        Multiple locations for the same book may have different lengths,
         which affects the correct ordering of quotes.
        For example, "l163" should be earlier than "l1466", but JSON puts the latter first.
        To fix this, we need to get the max length of location keys for each publication,
         and pad all of that publication's location keys that are shorter 
         with leading zeros after the initial letter.
    """
    
    for books in dict_new.values():
        for key,book in books.items():
            loc_length = longest_loc_length(book)
            book_new = pad_locs(book,loc_length)
            books[key] = book_new # can I do this within a loop??
    return dict_new


def longest_loc_length(book):
    """
        Return the length of the longest location key string.
    """
    
    loc_length = 0
    for loc_string in book.keys():
        if len(loc_string) > loc_length: loc_length = len(loc_string)
    
    return loc_length


def pad_locs(book,loc_length):
    """
        Pad location keys as necessary
    """
    
    book_new = {}
    for key,value in book.items():
        pad = loc_length - len(key) # how much we need to pad
        newkey=key
        while pad > 0:
            newkey = newkey[0] + "0" + newkey[1:]
            pad-=1
        book_new[newkey] = value
    
    return book_new


def progress(message,step,total):
    """
        Print progress.
    """
    
    print(message+str(int(step*100/total))+"%", end="\r")

"""
    Run main
"""
if __name__ == "__main__":
    do_clippings()
