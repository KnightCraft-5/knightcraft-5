#!/usr/bin/env python3
"""Build the "Güçlenme" (getting stronger) chapter - the gear power curve.

WHY ITS OWN TREE
Gems ARE the power curve of this pack, and until now nothing in the book
explained them: how to get dust, that sockets are added with a sigil, that gems
can be pulled back OUT of gear, or that the rarity ladder needs a bigger
Extended Crafting bench at each step. That is not act content - it runs
alongside every act - so it gets its own chapter.

All tasks are DETECTION (data.snbt sets default_consume_items:false), so players
keep what they show the book.

Ids use the 0007 segment, verified free across chapter/quest/task/reward space.
"""
import pathlib

CH = pathlib.Path(__file__).resolve().parent.parent / 'config/ftbquests/quests/chapters'
CHAPTER_ID = '1000000000000701'

# n, title_tr, subtitle_en, description_tr, description_en, item, x, y, deps, capstone
Q = [
    (1, 'Taş Tozu', 'Gem Dust', 'Her şey toza dönüşür. Ve tozdan yeniden doğar.',
     'Everything turns to dust. And from dust it is reborn.',
     'apotheosis:gem_dust', 0.0, 0.0, [], False),
    (2, 'Büyülü Levha', 'Gem-Fused Slate', 'Derin taş ve toz. Mühürlerin temeli.',
     'Deepslate and dust. The base of every sigil.',
     'apotheosis:gem_fused_slate', 2.0, 1.5, [1], False),
    (3, 'Yuva Mührü', 'Sigil of Socketing', 'Zırhına bir yuva daha aç. En fazla beş.',
     'Open one more socket in your gear. Five at most.',
     'apotheosis:sigil_of_socketing', 4.0, 0.5, [2], False),
    (4, 'Geri Çekme Mührü', 'Sigil of Withdrawal', 'Yanlış parçaya taktığın taşı geri al. Taş kaybolmaz.',
     'Pull gems back out of the wrong piece. Nothing is lost.',
     'apotheosis:sigil_of_withdrawal', 4.0, 2.5, [2], False),
    (5, 'Temel Tezgah', 'Basic Table', 'İlk tezgah. Çatlak taşlar burada doğar.',
     'The first bench. Cracked gems are born here.',
     'extendedcrafting:basic_table', 2.0, -1.5, [1], False),
    (6, 'İlk Taş', 'Your First Gem', 'Çatlak bir taş. Küçük ama başlangıç.',
     'A cracked gem. Small, but it begins here.',
     'apotheosis:gem', 4.0, -1.5, [5], False),
    (7, 'Gelişmiş Tezgah', 'Advanced Table', 'Nadir ve destansı taşlar için.',
     'For rare and epic gems.',
     'extendedcrafting:advanced_table', 6.0, -1.5, [6], False),
    (8, 'Seçkin Tezgah', 'Elite Table', 'Efsanevi taşlar bu tezgâhı ister.',
     'Mythic gems demand this bench.',
     'extendedcrafting:elite_table', 8.0, -1.5, [7], False),
    (9, 'Nihai Tezgah', 'Ultimate Table', 'Son tezgâh. Kusursuz taşların evi.',
     'The last bench. Home of perfect gems.',
     'extendedcrafting:ultimate_table', 10.0, -1.5, [8], False),
    (10, 'Yeniden Dövme', 'Reforging Table', 'Ekipmanını yeniden döv, yeni ekler bul.',
     'Reforge your gear and reroll its affixes.',
     'apotheosis:reforging_table', 2.0, 4.0, [1], False),
    (11, 'Hurdacı', 'Salvaging Table', 'İstemediğin taşı toza çevir. Hiçbir şey boşa gitmez.',
     'Turn unwanted gems back into dust. Nothing is wasted.',
     'apotheosis:salvaging_table', 4.0, 4.0, [10], False),
    (12, 'Kusursuz Taş', 'A Perfect Gem', 'Kadim bir taş. Beş yuva, beş taş, ve sen artık başkasın.',
     'An ancient gem. Five sockets, five gems, and you are something else.',
     'apotheosis:gem', 12.0, -1.5, [9, 3], True),
]

def block(n, tr, en, dtr, den, item, x, y, deps, cap):
    qid = f'20000000000007{n:02d}'
    tid = f'30000000000007{n:02d}'
    rid = f'40000000000007{n:02d}'
    dep = "\n".join(f'\t\t\t\t"20000000000007{d:02d}"' for d in deps)
    deps_field = f'\t\t\tdependencies: [\n{dep}\n\t\t\t]\n' if deps else ''
    shape = '\n\t\t\tshape: "hexagon"\n\t\t\tsize: 1.5d' if cap else ''
    xp = 600 if cap else 150
    nbt = ''
    if cap:
        nbt = '\n\t\t\t\tnbt: {affix_data:{rarity:"apotheosis:ancient"}}'
    return f'''		{{
{deps_field}			description: [
				"{dtr}"
				""
				"§7{den}§r"
			]
			icon: "{item}"
			id: "{qid}"{shape}
			rewards: [{{
				id: "{rid}"
				type: "xp"
				xp: {xp}
			}}]
			subtitle: "{en}"
			tasks: [{{
				id: "{tid}"
				item: "{item}"{nbt}
				type: "item"
			}}]
			title: "{tr}"
			x: {x}d
			y: {y}d
		}}'''

def main():
    body = "\n".join(block(*q) for q in Q)
    (CH / 'apotheosis.snbt').write_text(
        '{\n'
        '\tdefault_hide_dependency_lines: false\n'
        '\tdefault_quest_shape: ""\n'
        '\tfilename: "apotheosis"\n'
        '\tgroup: ""\n'
        '\ticon: "apotheosis:gem_dust"\n'
        f'\tid: "{CHAPTER_ID}"\n'
        '\torder_index: 9\n'
        '\tquest_links: [ ]\n'
        '\tquests: [\n'
        f'{body}\n'
        '\t]\n'
        '\ttitle: "Güçlenme"\n'
        '}\n', encoding='utf-8')
    print(f'wrote apotheosis chapter with {len(Q)} quests')

if __name__ == '__main__':
    main()
