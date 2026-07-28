#!/usr/bin/env python3
"""Split thematic side-content out of the act chapters into its own tree.

WHY
Ars Nouveau was 13 quests living inside act3 (the mining act), sprawling from
x=8 to x=22 and crowding the act's own line. It is optional side content with
exactly ONE external dependency, so it belongs in its own chapter where it can
be laid out as a readable tree and ignored by players who do not want magic.

Quest blocks are moved VERBATIM - only `x`, `y` and the root's `dependencies`
are rewritten. Ids are untouched, so existing player progress survives the move.
"""
import pathlib, re, sys

QDIR = pathlib.Path(__file__).resolve().parent.parent / 'config/ftbquests/quests'
CH = QDIR / 'chapters'

def split_quest_blocks(text):
    """Yield (start, end) spans of each top-level block inside `quests: [ ... ]`."""
    i = text.index('quests: [')
    i = text.index('[', i)
    depth, start, spans = 0, None, []
    j = i + 1
    while j < len(text):
        c = text[j]
        if c == '{':
            if depth == 0:
                start = j
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                spans.append((start, j + 1))
        elif c == ']' and depth == 0:
            break
        j += 1
    return spans

def qid_of(block):
    m = re.search(r'\bid:\s*"([0-9A-F]{16})"', block)
    return m.group(1) if m else None

def set_field(block, field, value):
    pat = re.compile(r'(\n\t*%s:\s*)([^\n]*)' % field)
    if pat.search(block):
        return pat.sub(lambda m: m.group(1) + value, block, count=1)
    return block.rstrip()[:-1].rstrip() + f'\n\t\t\t{field}: {value}\n\t\t}}'

def move(src_name, dst_name, ids, layout, chapter_id, order_index, title, icon, root_id):
    src = CH / f'{src_name}.snbt'
    text = src.read_text(encoding='utf-8')
    spans = split_quest_blocks(text)
    keep, taken = [], {}
    for a, b in spans:
        blk = text[a:b]
        q = qid_of(blk)
        if q in ids:
            taken[q] = blk
        else:
            keep.append((a, b))
    if len(taken) != len(ids):
        print(f'  WARNING: found {len(taken)} of {len(ids)} ids in {src_name}')

    # rebuild source without the taken blocks
    out, prev = [], None
    removed = [ (a,b) for a,b in spans if text[a:b] not in keep and qid_of(text[a:b]) in ids ]
    newtext = text
    for a, b in sorted(removed, reverse=True):
        line_start = newtext.rfind('\n', 0, a) + 1
        end = b
        while end < len(newtext) and newtext[end] in ' \t':
            end += 1
        if end < len(newtext) and newtext[end] == '\n':
            end += 1
        newtext = newtext[:line_start] + newtext[end:]
    src.write_text(newtext, encoding='utf-8')

    # build destination
    blocks = []
    for q in ids:
        blk = taken.get(q)
        if not blk:
            continue
        x, y = layout[q]
        blk = set_field(blk, 'x', f'{x}d')
        blk = set_field(blk, 'y', f'{y}d')
        if q == root_id:
            blk = re.sub(r'\n\t*dependencies:\s*\[[^\]]*\]', '', blk, count=1)
        blocks.append(blk)
    body = "\n".join(blocks)
    dst = CH / f'{dst_name}.snbt'
    dst.write_text(
        '{\n'
        '\tdefault_hide_dependency_lines: false\n'
        '\tdefault_quest_shape: ""\n'
        f'\tfilename: "{dst_name}"\n'
        '\tgroup: ""\n'
        f'\ticon: "{icon}"\n'
        f'\tid: "{chapter_id}"\n'
        f'\torder_index: {order_index}\n'
        '\tquest_links: [ ]\n'
        '\tquests: [\n'
        f'{body}\n'
        '\t]\n'
        f'\ttitle: "{title}"\n'
        '}\n', encoding='utf-8')
    print(f'  moved {len(blocks)} quests {src_name} -> {dst_name}')

ARS_LAYOUT = {
    '2000000000000B34': (0.0,  0.0),   # Çırak Büyücü (root)
    '2000000000000F02': (2.0,  0.0),   # Yazıcının Masası
    '2000000000000F03': (4.0,  0.0),   # İlk Biçim: Mermi
    '2000000000000F04': (6.0, -1.5),   # İlk Etki: Zarar
    '2000000000000F05': (6.0,  1.5),   # Kırma Büyüsü
    '2000000000000F06': (8.0,  0.0),   # Kaynak Taşı
    '2000000000000F07': (10.0,-1.5),   # Imbuement Chamber
    '2000000000000F08': (10.0, 1.5),   # Kaynak Altyapısı
    '2000000000000F10': (12.0,-3.0),   # Güçlendirme Glifleri
    '2000000000000F12': (12.0, 0.0),   # Kaçış Sanatı
    '2000000000000F13': (12.0, 3.0),   # Şifacı
    '2000000000000F14': (14.0, 0.0),   # Büyücünün Kitabı
    '2000000000000F16': (16.0, 0.0),   # Baş Büyücü
}

if __name__ == '__main__':
    move('act3_madenci', 'ars_nouveau', list(ARS_LAYOUT), ARS_LAYOUT,
         chapter_id='1000000000000B01', order_index=8,
         title='Büyü Sanatı', icon='ars_nouveau:novice_spell_book',
         root_id='2000000000000B34')
