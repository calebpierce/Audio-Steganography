"""

Members: Donovan Olivarez, Caleb Pierce, Sarah Rodriguez

"""

import argparse
import sys
import os
import math
from scipy.io import wavfile
from numpy import ndarray, int16


# ------ Config ------ #
HEADER_SIZE = 32
MAX_DIFF = 65535

# ------ Range Table Functions ------ #
def generate_range_table():
    """
    Generate a range table.
    This is used to determine how many bits to hide and what bit strings we hide.
    """
    range_table = []
    MAX_DIFF = 65535
    current = 1
    range_too_large = False

    # starting values for the range.
    range_size = 4
    remaining_size = 0

    range_table.append({'start': 0, 'end': 0, 'num_bits': 0, 'bits': ''})

    for bit in range(1, 16):
        # Get total number of ranges to create
        range_size = 2**bit

        # Create ranges
        for _ in range(range_size):
            if current + range_size > MAX_DIFF:
                range_too_large = True
                break

            # If we have room, create the table entry as normal
            end = current + range_size - 1
            range_table.append({'start': current, 'end': end, 'num_bits': bit})
            current = end + 1

        # We are actually done, so break out of the outer loop
        if current > MAX_DIFF:
            break

        # If we didn't break out in the previous condition, then we still have room to create a table entry, just with a smaller bit size.
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
    Get the number of bits we can hide using the specified difference.
    """
    for entry in range_table:
        if entry['start'] <= difference <= entry['end']:
            return entry['num_bits']
    print('difference not defined in range table, skipping sample.')
    return None


def get_target_range(bit_sequence: str, num_bits: int, range_table: list) -> tuple:
    """
    Get the target range that we will hide the message in using the 
    bit sequence and the number of bits we can use for hiding.
    """
    for entry in range_table:
        if num_bits == entry['num_bits'] and bit_sequence == entry['bits']:
            return (entry['start'], entry['end'])

    print('target range not found, skipping sample')
    return None


# ------ Decoding Lookup Functions ------ #
# Get the bit sequence by using the difference.
def get_bit_sequence(difference: int, range_table: list) -> str:
    for entry in range_table:
        if entry['start'] <= difference <= entry['end']:
            return entry['bits']
    print(f'bit sequence not found for difference value {difference}')
    return ''


# ------ Reading and Writing Functions ------ #
def read_wav(sample: str) -> ndarray:
    """
    Read a wav file. If a WAV file is not specified for the cover,
    the program will exit.
    """
    try:
        samplerate, data = wavfile.read(sample)
        return data, samplerate
    except ValueError:
        print('Incorrect file type. Must use a WAV file as a cover.')
        sys.exit(1)


def write_wav(wav_file_data: ndarray, samplerate: int, filename='output.wav') -> None:
    """
    Writes the final output.
    """
    wavfile.write(filename=filename, rate=samplerate, data=wav_file_data)


# ------ Helpers ------ #
def convert_message_to_bit_stream(hidden_message_file):
    """
    Reads in the message to hide, converts it to a string of bits.
    This is what the hide function uses when embedding the message.
    """
    with open(hidden_message_file, 'rb') as file:
        secret_message = file.read()
        return len(secret_message), "".join(f"{byte:08b}" for byte in secret_message)


# ------ Encoder ------ #
def hide(message, audio_cover, range_table, output='output.wav'):
    """
    - Convert message to bit stream
    - Read audio file
    - Get the difference between left and right channel
    - Use the difference to find # of bits to hide
    - Get # of bits from the message bit stream using python slicing
    - Use bit sequence to find the new target range in the range table.
    - Find the range value closest to our original difference
    - Find the modification value using the original diff and the new closest range value
    - Modify the right audio channel by the modification value to get our target difference

    The modified channel should now create the difference that maps to the bit sequence we are hiding.
    """

    # add a header with the size of the message.
    file_size_in_bytes, message_bit_stream = convert_message_to_bit_stream(hidden_message_file=message)
    header_bits = f'{file_size_in_bytes:0{int(HEADER_SIZE)}b}'
    message_bit_stream = header_bits + message_bit_stream

    data, sample_rate = read_wav(audio_cover)
    steg_data = data.copy()

    for i, sample in enumerate(data):
        left = sample[0]
        right = sample[1]
        diff = left - right
        current_msg_len = len(message_bit_stream)

        bits_to_hide = get_num_bits(difference=abs(diff), range_table=range_table)
        if bits_to_hide and bits_to_hide != 0:
            if current_msg_len <= 0:
                print("Message fully hidden.")
                break

            # check to see if we have enough bits in the message bit stream to cover what the 
            # algorithm has chosen.
            if current_msg_len < bits_to_hide:
                msg_chunk = message_bit_stream.ljust(bits_to_hide, '0')
            else:
                msg_chunk = message_bit_stream[:bits_to_hide]

            target_range = get_target_range(bit_sequence=msg_chunk, num_bits=bits_to_hide, range_table=range_table)
            if target_range == None:
                continue

            # Encode the message
            new_start, new_end = target_range

            # Find target range to hide our message
            target_range_list = [abs(diff), new_start, new_end]
            target_range_list.sort()

            # Get value that is numerically closest to the original difference
            closest_to_original = target_range_list[1]

            # Get modification value
            modification = right + (diff - closest_to_original)

            # Update the right audio channel
            steg_data[i, 1] = modification

            # Remove the bits we just encoded from the message bit stream
            message_bit_stream = message_bit_stream[bits_to_hide:]

    # if we are done going through samples but still have bits left in our message, we did not hide the full message.
    if len(message_bit_stream) > 0:
        print("Message not fully hidden.")


    steg_data.astype(int16)

    # Write the result
    write_wav(wav_file_data=steg_data, samplerate=sample_rate, filename=output)
    print(f"Message hidden in file: {output}")


# ------ Decoder ------ #
def extract(steg_wav, range_table, output='hidden_message'):
    """
    - Open up a steg audio file
    - Get header to get message size (know when to stop)
    - Reconstruct the message
    - Write out the message
    """
    decoded_message = ''
    message_size = None
    data, _ = read_wav(steg_wav)

    for i, sample in enumerate(data):
        # checks to see if we have enough bits for the header.
        # if so, we know how large our actual message is.
        if len(decoded_message) == HEADER_SIZE:
            message_size = int(decoded_message, 2)

        # Check if decoded message is the size of our message plus the header.
        # If we read in all the data needed for the message, we can stop here.
        if message_size is not None and (len(decoded_message) >= ((message_size * 8) + HEADER_SIZE)):
            break

        # decode by getting the difference.
        left = sample[0]
        right = sample[1]
        diff = left - right

        if diff == 0:
            continue

        bits = get_bit_sequence(difference=abs(diff), range_table=range_table)
        decoded_message += bits

    # Remove header from decoded message
    decoded_message = decoded_message[HEADER_SIZE:]

    # get our decoded bit string to a bytes object, then write the output.
    final_bits = decoded_message[:message_size * 8]
    byte_values = bytes([int(final_bits[i:i+8], 2) for i in range(0, len(final_bits), 8)])

    with open(output, 'wb') as file:
        file.write(byte_values)

    print(f"Message extracted to: {output}")


# ------ Main Entry with Argument Parsing ------ #
def main():
    parser = argparse.ArgumentParser(description='Audio Steganography Tool')
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-hide', action='store_true', help='Hide a message in the audio file')
    mode_group.add_argument('-extract', action='store_true', help='Extract a message from the audio file')

    # Hide mode
    parser.add_argument('-m', type=str, help='Message file to hide')
    parser.add_argument('-c', type=str, help='Cover WAV audio file')

    # Extract mode
    parser.add_argument('-s', type=str, help='Stego WAV audio file (for extraction)')

    # Common output
    parser.add_argument('-o', type=str, help='Output file (optional)')

    args = parser.parse_args()
    table = generate_range_table()
    full_range_table = generate_bit_sequences(range_table=table)

    if args.hide:
        if not args.m or not args.c:
            print("Error: -m <message file> and -c <coverfile> are required for hiding.")
            sys.exit(1)
        output_file = args.o if args.o else "output.wav"
        hide(message=args.m, audio_cover=args.c, range_table=full_range_table, output=output_file)

    elif args.extract:
        if not args.s:
            print("Error: -s <stego file> is required for extraction.")
            sys.exit(1)
        output_file = args.o if args.o else "hidden_message"
        extract(steg_wav=args.s, range_table=full_range_table, output=output_file)


if __name__ == '__main__':
    main()
