import re, json, sys, io
from time import strptime
from datetime import datetime

def output(json_string,f_out=None):
    """
        Print or file write
    """
    if f_out:
        ## Write
        with io.open(f_out,"w",encoding='utf-8') as f:
            f.write(json_string)
            
        return
    
    print(json_string)

def build_dict_line(line):
    """
        Convert the line to the new format.
        The current order is:
            0<title>,
            1<author>,
            2Loc.|on Page,
            3<loc or page>,
            4<??>,
            5<??>,
            6<day>,
            7<month>,
            8<date>,
            9<year>,
            10<hour>,
            11<minute>,
            12AM/PM,
            13<quote>
        New format:
            {
                "Daniel C. Dennett":  {
                    "From Bacteria to Bach and Back":   {
                        33
                    }
                }
            }
    """
    
    ##Timestamp
    # # line[9] # year
    # # line[7] # month (in words)
    # # line[8] # date
    # # line[10] # hour
    # # line[11] # minute
    # # line[12] # AM/PM
    year = int(line[9])
    month = int(strptime(line[7][:3],'%b').tm_mon)
    day = int(line[8])
    hour = int(line[10])
    if line[12] == "PM":
        hour = (hour + 12) % 24
    minute = int(line[11])
    date = datetime(year,month,day,hour,minute)
    
    ## Author format
    author = line[1]
    ## Get rid of backslashes
    author = author.replace('\\','')
    
    ## Page/location format
    if line[2] == "on Page":
        loc = "p"
    elif line[2] == "Loc.":
        loc = "l"
    else:
        loc = ""
    
    loc = loc + str(line[3])
    
    ## Quote formatting
    quote = line[13].replace('"','\\"')
    
    dict_line = {author:{line[0]:{loc:[{"quote":quote,"date":date.strftime("%Y%m%d-%H%M")}]}}}
    
    return dict_line

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
                        <day>,
                        <month>,
                        <date>,
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
                        <day>,
                        <month>,
                        <date>,
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
                    "Daniel C. Dennett":  {
                        "From Bacteria to Bach and Back":   {
                            
                        }
                    }
                }
            }
    """
    
    dict_new = {"notes_author":{}}
    for line in dict["notes_author"]:
        
        dict_line = build_dict_line(line)
        
        dict_new = add_line_to_dict_deep(dict_new,dict_line)
    
    
    return dict_new

    
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
        So we need to check the title and location to make sure it's not overwritten
    """
    author      = list(line.keys())[0]    # sfm python 3
    title       = list(line[author].keys())[0] # sfm python 3
    location    = list(line[author][title].keys())[0] # sfm python 3
    
    
    if author not in dict["notes_author"]:
        dict["notes_author"].update(line)
        return dict
    
    ## The author is already there
    if title not in dict["notes_author"][author]:
        dict["notes_author"][author].update(line[author])
        return dict
        
    ## The title is already there
    if location not in dict["notes_author"][author][title]:
        dict["notes_author"][author][title].update(line[author][title])
        return dict
    
    ## The location is already there
    ## Just need to add the entry
    dict["notes_author"][author][title][location] += line[author][title][location]
    return dict

    
def parse_raw(raw):
    """
        Convert Kindle clippings text file to JSON and print to JSON file
    """
    
    ## Regex parts
    title_regex = "(.+)"
    title_author_regex = "(.+) \((.+)\)"

    #loc_norange_regex = "(Loc.|on Page) ([0-9]+)"
    #loc_range_regex = "(Loc.|on Page) ([0-9]+)-([0-9]+)"
    loc_all_regex = "(Loc.|on Page) ([0-9]+)( |-([0-9]+)  )"
    #loc_all_regex = "(Loc.) ([0-9]+)( |-([0-9]+)  )"

    date_regex = "([a-zA-Z]+), ([a-zA-Z]+) ([0-9]+), ([0-9]+)"  # Date
    time_regex = "([0-9]+):([0-9]+) (AM|PM)"  # Time

    content_regex = "(.*)"
    footer_regex = "=+"

    #nl_re = "\r*\n"
    nl_re = "\n*"

    ## No author
    regex_noauthor_str =\
    title_regex + nl_re +\
    "- Highlight " + loc_all_regex + "\| Added on " +\
    date_regex + ", " + time_regex + nl_re +\
    content_regex + nl_re +\
    footer_regex
    
    ## Perform the regex for entries without an author
    regex_noauthor = re.compile(regex_noauthor_str)
    dict_noauthor = {"notes_noauthor":regex_noauthor.findall(raw)}
    
    ## Author
    regex_author_str =\
    title_author_regex + nl_re +\
    "- Highlight " + loc_all_regex + "\| Added on " +\
    date_regex + ", " + time_regex + nl_re +\
    content_regex + nl_re +\
    footer_regex
    
    ## Perform the regex for entries with an author
    regex_author = re.compile(regex_author_str)
    dict_author = {"notes_author":regex_author.findall(raw)}
    
    dict_all = dict_author
    dict_all.update(dict_noauthor)
    
    dict_all = organise(dict_all)
    
    json_all = json.dumps(dict_all, indent=4, sort_keys=True)
    
    return json_all

def do_clippings(f_in):
    """
        Wrapper
    """
    
    with open(f_in,"r",encoding='utf-8') as f:
        raw = f.read()
    
    ## Remove byte order marks if necessary
    # if raw[0] == '\xef':
        # raw = raw[1:]
    
    # if raw[0] == '\xbb':
        # raw = raw[1:]
    
    # if raw[0] == '\xbf':
        # raw = raw[1:]
    
    json_string = parse_raw(raw)
    
    output(json_string,"clippings.json")
    
    


if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        f_in = sys.argv[1]
    else:
        f_in = "My Clippings.txt"
    
    print(f_in)
    
    do_clippings(f_in)
    