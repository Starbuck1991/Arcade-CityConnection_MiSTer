"""Perfiles City Connection a partir de los tres rangos de MAME hiscore.dat."""
from pathlib import Path
import json
import re
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = [(0x55, 3, 0x00, 0x13), (0x43, 3, 0x00, 0x02), (0x900, 0xF0, 0x53, 0x90)]


def main():
    # Parámetros ya utilizados por el motor en Tecmo. La comprobación de
    # firmas, no este retardo heredado, determina cuándo restaurar la RAM.
    header = bytes.fromhex('00 00 FF FF 00 FF 00 02 00 02 00 01 00 FF 02 00')
    payload = header + b''.join(struct.pack('>IBBBB', addr, length, first, last, 0)
                                for addr, length, first, last in ENTRIES)
    size = sum(entry[1] for entry in ENTRIES)
    assert size == 246 and all(addr + length <= 0x1000 for addr, length, _, _ in ENTRIES)
    for source in (ROOT / 'releases').rglob('*.mra'):
        if 'Hiscore' in source.name:
            continue
        text = source.read_text(encoding='utf-8-sig')
        original = ET.fromstring(text)
        title = original.findtext('name')
        new_title = 'City Connection (Hiscore)' if original.findtext('setname') == 'citycon' else title.replace('(', '(Hiscore, ', 1)
        modified = re.sub(r'<name>.*?</name>', '<name>' + new_title + '</name>', text, count=1)
        modified = re.sub(r'<rbf>.*?</rbf>', '<rbf>CityConnection_Hiscore</rbf>', modified, count=1)
        rows = '\n'.join('      ' + ' '.join(f'{b:02X}' for b in payload[i:i + 16]) for i in range(0, len(payload), 16))
        block = ('\n  <!-- MAME hiscore.dat: citycon/citycona/cruisin; 246 bytes de RAM. -->\n'
                 '  <rom index="5" md5="none"><part>\n' + rows + '\n  </part></rom>\n'
                 f'  <nvram index="6" size="{size}"/>\n')
        modified = modified.replace('</misterromdescription>', block + '</misterromdescription>')
        target = source.with_name(new_title + '.mra')
        target.write_text(modified, encoding='utf-8')
        result = ET.fromstring(modified)
        for before, after in zip(original.findall('rom'), result.findall('rom')):
            before.tail = after.tail = None  # Ignorar separación XML exterior.
            assert ET.tostring(before) == ET.tostring(after)
        assert bytes.fromhex(result.find("rom[@index='5']/part").text) == payload
        print('Preparado: ' + target.name)
    profile = dict(source='https://github.com/mamedev/mame/blob/master/plugins/hiscore/hiscore.dat',
                   sets=['citycon', 'citycona', 'cruisin'], entries=ENTRIES, nvram_size=size)
    (ROOT / 'support/hiscore-profile.json').write_text(json.dumps(profile, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
