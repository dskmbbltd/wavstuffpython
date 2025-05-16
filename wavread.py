import struct
import sys
import time


class Wavread:
    def __init__(self, filename):
        self.filename = filename
        self.samplerate = None
        self.channels = None #Number of channels
        self.bits = None
        self.samples = []
        self.duration = None
        self.block_align = None

    def read(self, cmd):
        with open(self.filename, 'rb') as f:
            riff = f.read(12)
            if riff[:4] != b'RIFF' or riff[8:] != b'WAVE': # .WAV files begin with 'RIFF' .... 'WAVE'
                raise ValueError('Not a wav')
            else:
                print('dis be a wav fail')
            print(f'command was {cmd}')


            while True:
                chunk = f.read(8)
                if len(chunk) < 8:
                    break
                chunk_id, chunk_size = struct.unpack('<4sI', chunk)
                chunk_data = f.read(chunk_size)
        
                if chunk_id == b'fmt ': # Always get the info
                    self.parse_fmt_chunk(chunk_data)    

                if chunk_id == b'data':
                    if cmd == 'I':
                        self.get_duration(chunk_data)
                        self.print_info()
                        break
                    elif cmd == 'V':
                        self.parse_data_chunk(chunk_data)
                        for offset in range(0, len(self.samples), self.samplerate//100):
                            self.visualize(0.01, offset)
                            time.sleep(0.01)
                        break

    def parse_fmt_chunk(self, data):
        fmt_code, self.channels, self.samplerate, byte_rate, self.block_align, self.bits = struct.unpack('<HHIIHH', data[:16])
        

    def parse_data_chunk(self, data):
        if self.bits == 8:
            fmt = 'B'
        elif self.bits == 16:
            fmt = 'h'
        else:
            raise ValueError('Bit depth unsupported')
        
        num_samples = len(data) // self.block_align
        print(num_samples)
        samples = struct.unpack(f'{num_samples}{fmt}', data)

        if self.channels == 2:
            self.samples = list(zip(samples[0::2], samples[1::2])) # For interleaved data
        else:
            self.samples = list(samples)

        print(len(self.samples))


    def print_info(self):
        print('Audio information: \n'+
              f' Channels:{self.channels}\n Bits:{self.bits}\n Sample rate:{self.samplerate}\n Duration (scnds): {self.duration:.2f}')


    # Visualises a waveform of a given length of time, averaging n amount of samples.
    # Visualization will flicker if console height is less than the lines being drawn.
    def visualize(self, duration=0.01, offset=0):

        #Waveform visualization 'frame' dimensions        
        h = 20
        mid = 10
        columns = 48 ## Use even numbers.

        frame_width = columns*2+5

        if self.bits == 8:
            max=127
        elif self.bits == 16:
            max = 32767
        else:
            raise ValueError('Unsupported')
        
        if self.channels == 2:
            sample_chunk = [s[0] for s in self.samples] # Take L channel only
        else:
            sample_chunk = self.samples

        samples_amount = int(self.samplerate  * duration) # N of frames within a period of time
        samples_to_group = samples_amount // columns # How many samples will be collected and shown avg of in one column



        if self.bits == 8:
            samples_to_average = [s-127 for s in sample_chunk[offset:min(offset+samples_amount, len(sample_chunk))]] #8bit
        else:
            samples_to_average = sample_chunk[offset:min(offset+samples_amount, len(sample_chunk))] #16bit
        
        

        samples_to_visualize = [sum(samples_to_average[i:i+samples_to_group]) / samples_to_group # Get the values to be used in the visualization
                    for i in range(0, samples_amount, samples_to_group)
                    ]


        for line in range(h+4):
            sys.stdout.write('\x1b[1A')   # Move cursor up 1 line
            sys.stdout.write('\x1b[2K')   # Clear the entire line

        title = f'{self.filename}'.center(frame_width, ' ')
        info = f'Snap of {duration}s. Averaged {samples_amount} samples to {columns} columns at {samples_to_group} samples per column.'.center(frame_width, ' ')
        
        print(f'\033[1m{title}')
        print(f'\033[1m{info}')
        
        
        for h in reversed(range(h+1)):
            line = f'{h-mid}'.ljust(5,' ')
            for plottable in samples_to_visualize:
                p = (mid + int((plottable/max)*10))
                # print(p)
                line += ' *' if p == h else ' -'
            print(line)
        print(f'{offset / self.samplerate:.1f}s'.center(frame_width, ' '))

    # get the duration of the song in seconds
    def get_duration(self, data):

        self.duration = (len(data) // self.block_align ) / self.samplerate
