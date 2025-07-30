from scipy.io import wavfile
from numpy import empty
from numpy import ndarray, append, array, int16, seterr
import math
import time

# seterr(all='raise')
HEADER_SIZE = 32
# ------ Range Table Functions ------ #
# we can control how fast the ranges grow with a cmd parameter. This can show a capacity vs stealth tradeoff.
# for now, hardcoded.
def generate_range_table():
    """
    generate a range table. I don't think any input should be needed here yet.
    """
    range_table = []
    MAX_DIFF = 65535
    current = 1
    range_too_large = False

    # can this be an arg? 
    range_size = 4
    remaining_size = 0

    range_table.append({'start': 0, 'end': 0, 'num_bits': 0, 'bits': ''})

    for bit in range(1, 16):

        # get total number of ranges to create
        range_size = 2**bit

        # create ranges. If we are going out of bounds, we can 
        for _ in range(range_size):
            if current + range_size > MAX_DIFF:
                range_too_large = True
                break

            # if we have room, create the table entry as normal
            end = current + range_size - 1
            range_table.append({'start': current, 'end': end, 'num_bits': bit})
            current = end + 1

        # we are actually done, so break out of the outer loop.
        if current > MAX_DIFF:
            break

        # if we didn't break out in the previous condition, then we still have room to create a table entry, just with a smaller bit size.
        if range_too_large:
            remaining_size = MAX_DIFF - current

            if remaining_size > 0:
                hidable_bits = math.floor(math.log2(remaining_size))
                range_size = 2**hidable_bits
                end = current + range_size - 1
                range_table.append({'start': current, 'end': end, 'num_bits': hidable_bits})
                current = end + 1

    return range_table


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


def get_num_bits(difference: int, range_table: list) -> int:
    """
    get the number of bits we can hide using the specified difference.
    """
    for entry in range_table:
        if difference >= entry['start'] and difference <= entry['end']:
            return entry['num_bits']
        
    # if the diff wasn't found
    print('difference not defined in range table, skipping.')
    return None

def get_target_range(bit_sequence: str, num_bits: int, range_table: list) -> tuple:
    """
    get the target range that we will hide the message in using the 
    bit sequence and the number of bits we can use for hiding.

    Might be able to reduce this to just use the bit sequence param.
    """

    for entry in range_table:
        if num_bits == entry['num_bits'] and bit_sequence == entry['bits']:
            # we have found our target range
            return (entry['start'], entry['end'])
        
    print('target range not found')
    return None


# decoding lookup functions
    # get the bit sequence by using the difference, lookup function for decoding. Can maybe clean this up.

def get_bit_sequence(difference: int, range_table: list) -> str:
    for entry in range_table:
        if difference >= entry['start'] and difference <= entry['end']:
            return entry['bits']
        
    print(f'bit sequence not found for difference value {difference}')
    return ''

# ------ Reading and Writing Functions ------ #
def read_wav(sample: str) -> ndarray:
    """
    read a wav file. Should also add some validation here to make sure we are using the right cover files.
    """
    max = 0
    # 2d array, each row is one sample. the first column has values from the left channel, the second column from the right channel.
    samplerate, data = wavfile.read(sample)

    # print(data.shape[0] / samplerate)


    # this doesn't really matter right now. mostly for testing.
    for sample in data:
        left = sample[0]
        right = sample[1]
        
    return data, samplerate


def write_wav(wav_file_data: ndarray, samplerate: int) -> None:
    """
    writes the final output. It's unclear if this needs to be a seperate method yet.
    """
    wavfile.write(filename='output.wav', rate=samplerate, data=wav_file_data)


# ------ Helpers ------ #
def convert_message_to_bit_stream(hidden_message_file):
    with open(hidden_message_file, 'rb') as file:
        secret_message = file.read()
        return len(secret_message), "".join(f"{byte:08b}" for byte in secret_message)


# ------ Encoder ------ #
def hide(message, audio_cover, range_table):
    """
    - convert message to bit stream
    - read audio file
    - get difference between left and right channel
    - use difference to find # of bits to hide
    - get # of bits from the message bit stream.
    - use bit sequence to find the new target range
    - find the range value closest to our original difference. This should help us determine how much we need to modify our original difference.
    - find the modification value using the original diff and the new closest range value.
    - modify the right audio channel by the modification value to get our target difference.
    

    The modified channel should now create the difference that maps to the bit sequence we are hiding.
    """
    file_size_in_bytes, message_bit_stream = convert_message_to_bit_stream(hidden_message_file=message)

    # get file size in bytes for the decoder
    header_bits = f'{file_size_in_bytes:0{int(HEADER_SIZE)}b}'

    # add the header with the message size to the beginning of the message.
    message_bit_stream = header_bits + message_bit_stream
        

    data, sample_rate = read_wav(audio_cover)
    steg_data = data.copy()

    for i, sample in enumerate(data):
        left = sample[0]
        right = sample[1]

        # get difference
        diff = left - right

        # get bits to hide using a range table helper function
        bits_to_hide = get_num_bits(difference=abs(diff), range_table=range_table)

        if bits_to_hide != 0:

            # if there is no more message to hide, then stop.
            if message_bit_stream == '':
                print("message fully hidden, exiting.")
                break
            
            # update the bits if the message length is shorter than what we calculated. This may happen towards the end of the process.
            if len(message_bit_stream) < bits_to_hide:
                last_bits = message_bit_stream
                msg_chunk = last_bits.ljust(bits_to_hide, '0')
            else:
                msg_chunk = message_bit_stream[:bits_to_hide]


            # encode the message
            new_start, new_end = get_target_range(bit_sequence=msg_chunk, num_bits=bits_to_hide, range_table=range_table)

            # find target range to hide our message
            target_range_list = [abs(diff), new_start, new_end]
            target_range_list.sort()

            # get value that is numerically closest to the original difference.
            closest_to_original = target_range_list[1]

            # get modification value. 
            modification = right + (diff - closest_to_original)

            # update the right audio channel
            steg_data[i,1] = modification

            # remove the bits we just encoded from the message bit stream
            message_bit_stream = message_bit_stream.replace(msg_chunk, '', count=1)

        steg_data.astype(int16)
    # write the result
    write_wav(wav_file_data=steg_data, samplerate=sample_rate)

    print("Done")

# ------ Decoder ------ #
def extract(steg_wav, range_table):
    """
    - open up a steg audio file.
    - get header to get message size (know when to stop)
    - reconstruct the message
    - write out the message
    """

    decoded_message = ''
    message_size = None

    data, _ = read_wav(steg_wav)
    for i, sample in enumerate(data):
        if len(decoded_message) == HEADER_SIZE:
            message_size = int(decoded_message, 2)

        if message_size != None and (len(decoded_message) >= ((message_size * 8) + HEADER_SIZE)):
            break

        left = sample[0]
        right = sample[1]
        diff = left - right

        if diff == 0:
            continue

        bits = get_bit_sequence(difference=abs(diff), range_table=range_table)
        decoded_message += bits

    
    # remove header from decoded message:
    decoded_message = decoded_message.replace(decoded_message[:HEADER_SIZE], '', count=1)
    # print(len(decoded_message))

    with open('hidden_message', 'wb') as file:
         # Write the bytes to create the new file
        final_bits = decoded_message[:message_size * 8]
        byte_values = bytes([int(final_bits[i:i+8], 2) for i in range(0, len(final_bits), 8)])
        file.write(byte_values)

# ------ Main Program------ #

table = generate_range_table()
full_range_table = generate_bit_sequences(range_table=table)

# check some of the data in the range table (for debugging only)
# for entry in full_range_table:
#     print(entry)


# encode/decode testing.
# hide(message='hello.txt', audio_cover='Three Evils (Embodied in Love and Shadow)_Sample.wav', range_table=full_range_table)
# hide(message='hello.txt', audio_cover='Mozart_Sample.wav', range_table=full_range_table)
hide(message='hello.txt', audio_cover='Swear_Sample.wav', range_table=full_range_table)
time.sleep(3)
extract(steg_wav='output.wav', range_table=full_range_table)
