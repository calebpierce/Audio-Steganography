## What you Need
- Python 3
    - scipy https://scipy.org/install/#installing-with-pip 
    - numpy

## Example Usage

### Working Examples, Not Noticable
python main.py -hide -m messages/hello.txt -c covers/3E.wav -o wav_hidden/3E_hidden.wav
python main.py -extract -s wav_hidden/3E_hidden.wav -o extracted_messages/3E_ext.txt


### Working, Very Noticable
python main.py -hide -m messages/CoatCheck.jpg -c covers/Mozart_Sample.wav -o wav_hidden/mozart_hidden.wav
python main.py -extract -s wav_hidden/mozart_hidden.wav -o extracted_messages/mozart_ext.jpg

python main.py -hide -m messages/CoatCheck.jpg -c covers/Swear_Sample.wav -o wav_hidden/swear_hidden.wav
python main.py -extract -s wav_hidden/swear_hidden.wav -o extracted_messages/swear_ext.jpg

### Known Issues
- The sample WAV 'Track4_Sample.wav' has some index out of bounds errors that are not handled. Using this sample does not currently work.
- Hiding some larger messages take a very long time. This is likely due to some inefficient lookups, or general inefficiencies in the range table.
- The range table has some bugs when higher difference values are encountered. It handles positive values at the moment, but should be adjusted to handle negative values due to the nature of 16-bit audio.