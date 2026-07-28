#!/usr/bin/env python3
"""Add a kill quest for every boss, into the act chapter it belongs to.

The book had only 5 kill/advancement tasks across 133 - progression was almost
entirely "hand in materials". Now that 76 bosses are tiered by act, each one gets
a quest in its act, so the book tracks deeds rather than purchases.

ID SCHEME
Existing book uses 2...A<act><n> for quests, 3...B<act><n> for tasks. Boss quests
take the verified-free 200000000000C<act><nn> range (and 3.../4... for task and
reward), which collides with nothing - checked against every id in the book.

Quests are DETECTION, never consuming: data.snbt has default_consume_items:false
and a kill task takes nothing anyway.

Run:  tools/gen_boss_quests.py [--dry-run]
"""
import pathlib
import re
import sys

INSTANCE = pathlib.Path(__file__).resolve().parent.parent
CHAPTERS = INSTANCE / "config" / "ftbquests" / "quests" / "chapters"

ACT_FILE = {
    2: "act2_gezgin", 3: "act3_madenci", 4: "act4_avci", 5: "act5_arena",
    6: "act6_cehennem", 7: "act7_ejderha", 8: "act8_kadim",
}

# entity -> (display name, Turkish flavour line, English flavour line, icon item)
# Icons deliberately use a vanilla or definitely-present item; a missing icon id
# renders as a purple-black cube and looks broken.
BOSSES = {
    2: [("minecraft:ravager", "Yıkıcı", "The Ravager", "minecraft:saddle"),
        ("born_in_chaos_v1:lord_pumpkinhead", "Lord Pumpkinhead", "Lord Pumpkinhead", "minecraft:carved_pumpkin"),
        ("born_in_chaos_v1:sir_the_headless", "Sir The Headless", "Sir The Headless", "minecraft:iron_sword"),
        ("born_in_chaos_v1:supreme_bonescaller", "Supreme Bonescaller", "Supreme Bonescaller", "minecraft:bone")],
    3: [("cataclysm:amethyst_crab", "Ametist Yengeç", "Amethyst Crab", "minecraft:amethyst_shard"),
        ("cataclysm:kobolediator", "Kobolediator", "Kobolediator", "cataclysm:kobolediator_skull"),
        ("born_in_chaos_v1:nightmare_stalker", "Kabus Avcısı", "Nightmare Stalker", "born_in_chaos_v1:nightmare_claw"),
        ("iceandfire:troll", "Trol", "Troll", "minecraft:stone_axe")],
    4: [("mowziesmobs:ferrous_wroughtnaut", "Demir Muhafız", "Ferrous Wroughtnaut", "mowziesmobs:wrought_axe"),
        ("cataclysm:the_prowler", "Sinsi Avcı", "The Prowler", "minecraft:iron_ingot"),
        ("legendary_monsters:overgrown_colossus", "Yosunlu Devasa", "Overgrown Colossus", "minecraft:moss_block"),
        ("legendary_monsters:beheaded_knight", "Başsız Şövalye", "Beheaded Knight", "minecraft:iron_helmet")],
    5: [("mowziesmobs:frostmaw", "Buzpençe", "Frostmaw", "minecraft:packed_ice"),
        ("cataclysm:coralssus", "Mercan Devi", "Coralssus", "cataclysm:coral_chunk"),
        ("iceandfire:myrmex_queen", "Myrmex Kraliçesi", "Myrmex Queen", "minecraft:honeycomb"),
        ("legendary_monsters:frostbitten_golem", "Donmuş Golem", "Frostbitten Golem", "minecraft:blue_ice"),
        ("cataclysm:wadjet", "Wadjet", "Wadjet", "minecraft:sand")],
    6: [("cataclysm:ignis", "Ignis", "Ignis, Lord of Fire", "cataclysm:ignitium_ingot"),
        ("cataclysm:netherite_monstrosity", "Netherit Canavarı", "Netherite Monstrosity", "minecraft:netherite_ingot"),
        ("cataclysm:ancient_remnant", "Kadim Kalıntı", "Ancient Remnant", "minecraft:sandstone"),
        ("mowziesmobs:umvuthi", "Umvuthi", "Umvuthi, the Sunbird", "minecraft:gold_ingot"),
        ("legendary_monsters:lava_eater", "Lav Yiyen", "Lava Eater", "minecraft:magma_block")],
    7: [("iceandfire:fire_dragon", "Ateş Ejderhası", "Fire Dragon", "iceandfire:fire_dragon_heart"),
        ("iceandfire:ice_dragon", "Buz Ejderhası", "Ice Dragon", "iceandfire:ice_dragon_heart"),
        ("iceandfire:lightning_dragon", "Yıldırım Ejderhası", "Lightning Dragon", "iceandfire:lightning_dragon_heart"),
        ("iceandfire:hydra", "Hidra", "The Hydra", "minecraft:dragon_breath"),
        ("cataclysm:the_leviathan", "Leviathan", "The Leviathan", "cataclysm:void_core"),
        ("cataclysm:scylla", "Scylla", "Scylla", "minecraft:trident"),
        ("mowziesmobs:sculptor", "Tongbi", "Tongbi, the Sculptor", "minecraft:clay"),
        ("alexsmobs:void_worm", "Boşluk Solucanı", "Void Worm", "minecraft:ender_eye"),
        ("iceandfire:cyclops", "Tepegöz", "Cyclops", "minecraft:beef")],
    8: [("cataclysm:the_harbinger", "Habercinin Sonu", "The Harbinger", "cataclysm:witherite_block"),
        ("cataclysm:ender_guardian", "Ender Muhafızı", "Ender Guardian", "minecraft:end_crystal"),
        ("cataclysm:maledictus", "Maledictus", "Maledictus", "minecraft:phantom_membrane"),
        ("legendary_monsters:the_obliterator", "Yok Edici", "The Obliterator", "minecraft:netherite_scrap"),
        ("legendary_monsters:posessed_paladin", "Ele Geçirilmiş Şövalye", "Possessed Paladin", "minecraft:netherite_chestplate"),
        ("threateningly_mobs:hypocritical_saint", "İkiyüzlü Aziz", "Hypocritical Saint", "minecraft:totem_of_undying"),
        ("legendary_monsters:annihilation_pursuer", "Yok Ediş Takipçisi", "Annihilation Pursuer", "minecraft:echo_shard")],
}

XP_BY_ACT = {2: 150, 3: 250, 4: 400, 5: 650, 6: 900, 7: 1400, 8: 2000}

# Each act's entry quest. Sub-boss quests hang off it, so they only unlock once
# the player has actually reached that act.
ACT_ENTRY = {a: f"2000000000000A{a}1" for a in range(2, 9)}

# The act capstone is the LAST entry in each act's boss list. It depends on every
# sub-boss in the act, so the act's big fight is gated behind clearing the rest -
# that is the hierarchy, not just a flat pile of optional kills.



# Sub-bosses wrap into columns of ROWS instead of one tall stack. Act 7 has 8 of
# them; stacked at 1.5 apart that column ran from y 4 to y 14.5 while the rest of
# the tree sat at y -3..2, so the act rendered as a thin ribbon nobody could read.
ROWS = 4
COL_W = 2.0
ROW_H = 1.5
BASE_X = 9.0


def boss_pos(n, capstone, total_subs):
    """Grid position for sub-boss n (1-based); the capstone sits right of the grid."""
    cols = max(1, -(-total_subs // ROWS))
    if capstone:
        return BASE_X + cols * COL_W, 0.0
    col, row = divmod(n - 1, ROWS)
    return BASE_X + col * COL_W, -((ROWS - 1) * ROW_H) / 2 + row * ROW_H


def quest_snbt(entity, tr_name, en_name, icon, act, n, deps, capstone, total_subs):
    qid = f"200000000000C{act}{n:02d}"
    tid = f"300000000000C{act}{n:02d}"
    rid = f"400000000000C{act}{n:02d}"
    x, y = boss_pos(n, capstone, total_subs)
    dep_lines = "\n".join(f'\t\t\t\t"{d}"' for d in deps)
    xp = XP_BY_ACT[act] * (3 if capstone else 1)
    extra = '\n\t\t\tshape: "hexagon"\n\t\t\tsize: 1.5d' if capstone else '\n\t\t\tshape: "square"'
    tr_desc = ("Bu perdenin son sınavı. Diğer canavarları geçtiysen hazırsın."
               if capstone else f"{tr_name} avına çık.")
    en_desc = ("The act's final trial. If you cleared the rest, you are ready."
               if capstone else f"Hunt down the {en_name}.")
    return f'''		{{
			dependencies: [
{dep_lines}
			]
			description: [
				"{tr_desc}"
				""
				"§7{en_desc}§r"
			]
			icon: "{icon}"
			id: "{qid}"{extra}
			rewards: [{{
				id: "{rid}"
				type: "xp"
				xp: {xp}
			}}]
			subtitle: "{en_name}"
			tasks: [{{
				entity: "{entity}"
				id: "{tid}"
				type: "kill"
				value: 1L
			}}]
			title: "{tr_name}"
			x: {x}d
			y: {y}d
		}}'''


def main():
    dry = "--dry-run" in sys.argv
    total = 0
    for act, bosses in BOSSES.items():
        path = CHAPTERS / f"{ACT_FILE[act]}.snbt"
        text = path.read_text(encoding="utf-8")
        entry = ACT_ENTRY[act]
        subs = bosses[1:]      # capstone is written first in each list
        cap  = bosses[0]
        new = [quest_snbt(e, tr, en, ic, act, i + 1, [entry], False, len(subs))
               for i, (e, tr, en, ic) in enumerate(subs)]
        sub_ids = [f"200000000000C{act}{i+1:02d}" for i in range(len(subs))]
        e, tr, en, ic = cap
        new.append(quest_snbt(e, tr, en, ic, act, len(bosses), sub_ids, True, len(subs)))
        # splice before the final "\t]" that closes the quests: [ ... ] array
        idx = text.rindex("\n\t]")
        text = text[:idx] + "\n" + "\n".join(new) + text[idx:]
        if not dry:
            path.write_text(text, encoding="utf-8")
        total += len(new)
        print(f"  {ACT_FILE[act]:16} +{len(new)} boss quests")
    print(f"\n{'would add' if dry else 'added'} {total} boss kill quests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
