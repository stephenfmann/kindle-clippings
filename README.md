# Kindle Clippings

Convert "My Clippings.txt" to JSON format.

### What is this?
If you have a classic Kindle, you can highlight sections of text when reading. Those highlights are stored on the Kindle in a file called "My Clippings.txt". 

This script converts the data in that file to JSON format, for ease of browsing.

### How to run?

Python 3.6.4

`python clippings.py [<filename>]`

The default is "My Clippings.txt"

Output file is in the format:

```json
{
    notes_author": {
        "<author>": {
            "<title>" {
                "<location/page>" : [
                    {
                        "date": "YYYYMMDD-HHMM",
                        "quote": "<quote text>"
                    }
                ]
            }
        }
    }
}
```
