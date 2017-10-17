ND = 'NODATA'


def hexbyte(byte):
    def hexwrd(x):
        return '{:02X}'.format(x)
    return ' '.join(hexwrd(a) if a != ND else '**' for a in byte)


def asciibyte(byte):
    return ''.join(chr(a) if (a > 32 and a < 127) else '.' for a in byte)


def view(packet):
    b = []
    w = []
    words = []
    for a in packet:
        b.append(ord(a))
        if len(b) == 8:
            w.append(b)
            b = []
            if len(w) == 2:
                words.append(w)
                w = []
    # Pad any missing byts with 0 to make both words
    if b:
        while len(b) < 8:
            b.append(ND)
        w.append(b)
    if w:
        if len(w) == 1:
            w.append([ND] * 8)
        words.append(w)
    for word in words:
        hword, lword = word
        line_parts = [
            hexbyte(hword),
            '  ',
            hexbyte(lword),
            '    ',
            asciibyte(hword),
            '  ',
            asciibyte(lword)
        ]
        print(''.join(line_parts))


if __name__ == '__main__':
    with open('packet.txt', 'rb') as fp:
        packet = fp.read()
    view(packet)
