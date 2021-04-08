# Kindle Clippings

Convert "My Clippings.txt" to JSON format.

## What is this?
If you have a classic Kindle, you can highlight sections of text when reading. Those highlights are stored on the Kindle in a file called "My Clippings.txt". 

This script converts the data in that file to JSON format, for ease of browsing.

## How to run?

Python 3.7.3

`python clippings.py [-i <input filename> -o <output filename>]`

If you do not supply \<input filename\>, the script defaults to "in/My Clippings.txt" which assumes you have a directory called "in" inside the directory where you put clippings.py.

If you do not supply \<output filename\>, the script defaults to "out/clippings.json" which assumes you have a directory called "out" inside the directory where you put clippings.py.

**Warning!** The script will overwrite \<output filename\> without warning.

Output file is in the format:

```json
{
    "<author>": {
        "<title>" {
            "<location/page>" : [
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

## How to get Kindle clippings when the connection is dodgy

My kindle is *old*. It sometimes doesn't connect to my computer for long enough to allow me to manually copy "My Clippings.txt". You can get around this. On Windows machines, do the following:

1. Plug in kindle
2. Open command prompt cmd.exe
3. Type "E:\documents\My Clippings.txt" (or whichever drive letter your kindle is under)
4. Save the file that opens (should open with your default text editor)
