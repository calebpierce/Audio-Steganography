from scipy.io import wavfile
from numpy import ndarray
import math



# ------ Range Table Functions ------ #
# we can control how fast the ranges grow with a cmd parameter. This can show a capacity vs stealth tradeoff.
# for now, hardcoded.
def generate_range_table():
    """
    generate a range table. I don't think any input should be needed here yet.
    """
    range_table = []

    MAX_DIFF = 65536

    # create range table entries until we hit max diff
    current = 1

    # can this be an arg? 
    range_size = 4

    while current <= MAX_DIFF:

        for i in range(16):

            # start of the range for the entry
            start = current

            # getting the value for the end of the range for this entry.
            end = min((start + range_size - 1), MAX_DIFF)

            current_entry_size = end - start + 1

            # initialize num_bits variable before going into conditionals
            num_bits = 0
            
            if range_size <= current_entry_size:
                # normal case, we can create a full size entry for the table.

                # we need three things for the table:
                # start, end, # of bits, actual bit sequence.
                num_bits = math.log2(range_size)

                range_table.append(
                    {
                        "start": start,
                        "end": end,
                        "num_bits": num_bits,
                        "bits": None
                    }
                )

                current = end + 1

            elif current_entry_size > 0:
                # we can't create a full range size, so find the correct size that we CAN hide.
                num_bits = math.floor(math.log2(current_entry_size))

                if num_bits > 0:
                    power_of_2_size = 2**num_bits
                    end = start + power_of_2_size - 1

                    range_table.append({
                        'start': start,
                        'end': end,
                        'num_bits': num_bits,
                        'bits': None
                    })
                    current = end + 1

            else:
                break

        range_size *= 2

    # handle negative ranges
    negative_table = []
    for entry in reversed(range_table):
        negative_table.append({
            'start': -entry['end'],
            'end': -entry['start'],
            'num_bits': entry['num_bits'],
            'bits': None
        })
        
    # zero range
    zero_range = [{
        'start': 0,
        'end': 0,
        'num_bits': 0, # Cannot hide data
        'bits': None
    }]

    return negative_table + zero_range + range_table


def generate_bit_sequences(range_table):
    counters = {}

    for entry in range_table:
        num_bits = entry['num_bits']

        if num_bits == 0:
            continue

        # If we see this bit length for the first time, initialize its counter
        if num_bits not in counters:
            counters[num_bits] = 0
        
        # Get the current ID and format it as a binary string with leading zeros
        current_id = counters[num_bits]
        bit_string = f'{current_id:0{int(num_bits)}b}'
        
        # Assign the bit string to the table entry
        entry['bits'] = bit_string
        
        # Increment the counter for the next range of this size
        counters[num_bits] += 1
        
    return range_table

        

table = generate_range_table()
full_range_table = generate_bit_sequences(range_table=table)

# check some of the data in the range table
for i in range(10000):
    print(full_range_table[i])


# ------ Reading and Writing Functions ------ #
def read_wav(sample: str) -> ndarray:
    """
    read a wav file. Should also add some validation here to make sure we are using the right cover files.
    """

    # 2d array, each row is one sample. the first column has values from the left channel, the second column from the right channel.
    samplerate, data = wavfile.read(sample)

    print(data.shape[0] / samplerate)


    # this doesn't really matter right now.
    for sample in data:
        left = sample[0]
        right = sample[1]
        print(sample)

    return data, samplerate


def write_wav(wav_file_data: ndarray, samplerate: int) -> None:
    """
    writes the final output. It's unclear if this needs to be a seperate method yet.
    """
    wavfile.write(filename='output.wav', rate=samplerate, data=wav_file_data)


# uncomment to read a sample and immediately write it back. It should be the exact same sample. You'll need to change the filename.
# wav_file_data, samplerate = read_wav('sample1.wav')
# write_wav(wav_file_data=wav_file_data, samplerate=samplerate)
