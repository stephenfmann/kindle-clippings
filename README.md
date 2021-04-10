# Kindle Clippings

Convert "My Clippings.txt" to JSON format.

## What is this?
If you have a classic Kindle, you can highlight sections of text when reading. Those highlights are stored on the Kindle in a file called "My Clippings.txt". 

This script converts the data in that file to JSON format, for ease of browsing.

## How to run?

Python 3.7.3

`python clippings.py [-i <input filepath>] [-o <output filepath> [-s <substitutions filepath>] [-z]`

+ If you do not supply \<input filename\>, the script defaults to "in/My Clippings.txt" which assumes you have a directory called "in" inside the directory where you put clippings.py.
+ If you do not supply \<output filename\>, the script defaults to "out/clippings.json" which assumes you have a directory called "out" inside the directory where you put clippings.py.
+ \<substitutions filepath\>: a json file with format specified below.
+ -z: timezone flag. If set, the user's current timezone will be added to all timestamps. Note that this is the timezone of the system running this script, not the Kindle system (i.e. the script does **not** extract timezone information from the clippings file itself).

**Warning!** The script will overwrite \<output filename\> without warning.

Output file is in the format:

```json
{
    "<author>": {
        "<title>": {
            "<location/page>": [
                {
                    "date": "YYYY-MM-DDTHH:MM",
                    "quote": "<quote text>"
                }
            ]
        }
    }
}
```

Double quote marks within a quote are prefaced with a backslash, otherwise the JSON would be invalid.

Quotes without an author are stored under the dummy author name ZZNOAUTHOR.

## Substitutions

The substitution file must be a json file with the following format:

```json
[
    {
        "old":  {
            "author":   "<original author>",
            "title":    "<original title>"
        },
        "new":  {
            "author":   "<author to be used>",
            "title":    "<title to be used>"
        }
    },
    {...},
    {...},
    ...
]
```

All entries with the author **and** title specified by an object in this file will have **both author and title** replaced with the author and title of the "new" element.

## How to get Kindle clippings when the connection is dodgy

My kindle is *old*. It sometimes doesn't connect to my computer for long enough to allow me to manually copy "My Clippings.txt". You can get around this. On Windows machines, do the following:

1. Plug in kindle
2. Open command prompt cmd.exe
3. Type "E:\documents\My Clippings.txt" (or whichever drive letter your kindle is under)
4. Save the file that opens (should open with your default text editor)
