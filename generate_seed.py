import os
import binascii


def generate_seed(string_len, count):
    file_name = 'seeds.csv'

    f = open(file_name, 'w')

    for x in range(count):
        f.write(binascii.b2a_hex(os.urandom(int(string_len/2))).decode('utf-8'))
        f.write('\n')

    f.close()


if __name__ == '__main__':
    generate_seed(30, 10500)
