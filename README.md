Team #20 Feedback
--- i know a lot of papers say convert secret message to a bitstream. All that
means is that we read the file into memory and access it one (or multiple) bits at
a time.

--- read cover. read message. don't need the "loop" step since the line going back
up signifies a loop

--- instead of "hide specified number of bits" say what you actually need to do. I
suspect you have to add/sub from either left/right samples so that the difference
encodes the message bits.

--- given that you will have to change, whenever the difference is zero, that could
encode a zero bit, otherwise you can adjust to make the difference a 1. So there
don't need to be any invalid differences where you hide none

--- make sure when you make adjustments that the new difference is in the same
range as the old difference

--- also have a check if there are more samples - if not, output "message not fully
hidden" or something like that - either way, save the output file

--- for the range, i suspect you'll take the floor{log2( |difference| )} to get
number of bits
so if a range is 8 to 15, then you can hide 3 bits and still stay in that range.
8=1000 in binary, 15=1111, so you can change the 3 bits to anything and still be in
the range.

--- here is the fun part, allow for a "fudge factor" so the encoder can jump
ranges. if the fudge factor is 0, you can't change. if it's one, you can jump up
one range. If the difference is 15, you could hide 4 bits, BUT you must make sure
the new difference will be in the 4-bit range

--- ultimately, we want to be sure that you can hide enough data TO be audible so
that we can test the limits (capacity/perceptibility) of this technique - the fudge
factor would be a user input

--- "Audacity" is a free program and great for working with audio file


## TODO:
- Range Table Generation (Sort of done, but may need a bit more testing)
- Encoder
- Decoder
- Argparse to make it a command line program with args https://docs.python.org/3/library/argparse.html
- Testing of Hiding and Extraction
- Analysis
- Report
