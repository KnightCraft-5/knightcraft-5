// Tech recipe hardening, tiered to the 8-act progression.
//
// Three jobs:
//   1. Price the items PMMO cannot gate. Upgrades that slot into a GUI (magnets,
//      pipe upgrades, stack upgrades) never fire a USE hook, so cost is the only
//      lever that reaches them.
//   2. Harden the FOUNDATION. Andesite alloy, water wheels and casings were
//      near-free, which made every gate downstream of them shallow.
//   3. Make tech consume dungeon loot, so automation is paid for in adventure.
//
// Artifacts used here are deliberately DIFFERENT from the ones the quest book
// asks for as turn-ins -- quest tasks consume the item, and a recipe competing
// with a progression gate for the same drop turns a gate into a grind.
//
// Artifact tiers, all 100% guaranteed uncraftable drops:
//   act 5  cataclysm:coral_chunk           Coralssus       160 hp miniboss
//   act 5  cataclysm:amethyst_crab_shell   Amethyst Crab   200 hp miniboss
//   act 7  cataclysm:void_core             Ender Golem     150 hp miniboss
//   act 7  legendary_monsters:frozen_rune  Frostbitten Golem
//   act 8  legendary_monsters:eye_crystal  Annihilation Pursuer
//   act 8  born_in_chaos_v1:lifestealer_bone
//   act 8  legendary_monsters:portal_shard The Obliterator
//   act 8  alexsmobs:void_worm_mandible    Void Worm

ServerEvents.recipes(event => {

	// ================================================================
	// ACT III - foundation. Andesite alloy is the root of everything.
	// ================================================================
	// Was: 2 andesite + 2 iron NUGGETS -> 1. Roughly a fifth of an ingot.
	// Now costs a full ingot, so the whole tree above it inherits real weight.
	event.remove({ output: 'create:andesite_alloy' })
	event.shaped('create:andesite_alloy', [
		'BA',
		'AB'
	], {
		A: 'minecraft:andesite',
		B: '#forge:ingots/iron'
	})

	// ================================================================
	// ACT IV - water power. Was 8 planks + a shaft, i.e. free.
	// ================================================================
	event.remove({ output: 'create:water_wheel' })
	event.shaped('create:water_wheel', [
		'ASA',
		'SCS',
		'ASA'
	], {
		A: 'create:andesite_alloy',
		S: '#minecraft:planks',
		C: 'create:shaft'
	})

	// ================================================================
	// CASINGS - the real chokepoint. Every Create machine needs one, so
	// tying casings to dungeon loot means tech consumption scales with how
	// much you build, and never stops requiring raids.
	//
	// Vanilla casings were create:item_application (right-click a stripped
	// log with the material). That recipe type takes exactly two ingredients,
	// so it is removed entirely and replaced with crafted recipes.
	//
	// Currencies chosen because they are REPEATABLE per raid, not one-off
	// trophies -- obelisk essences drop 3-6 guaranteed per obelisk clear,
	// and relics drop 3 guaranteed per Dungeon Realm uber boss.
	// ================================================================
	event.remove({ output: 'create:andesite_casing' })
	event.shaped('2x create:andesite_casing', [
		'LAL',
		'AOA',
		'LAL'
	], {
		L: '#forge:stripped_logs',
		A: 'create:andesite_alloy',
		O: 'ancient_obelisks:ancient_wrath'
	})

	event.remove({ output: 'create:copper_casing' })
	event.shaped('2x create:copper_casing', [
		'LCL',
		'COC',
		'LCL'
	], {
		L: '#forge:stripped_logs',
		C: '#forge:ingots/copper',
		O: 'ancient_obelisks:ancient_envy'
	})

	event.remove({ output: 'create:brass_casing' })
	event.shaped('2x create:brass_casing', [
		'LBL',
		'BRB',
		'LBL'
	], {
		L: '#forge:stripped_logs',
		B: '#forge:ingots/brass',
		R: 'dungeon_realm:general_relic'
	})

	// ================================================================
	// ACT V - processing tier. First machines that multiply output,
	// so each now costs a miniboss drop.
	// ================================================================
	event.remove({ output: 'create:mechanical_mixer' })
	event.shaped('create:mechanical_mixer', [
		'S ',
		'CR',
		'I '
	], {
		S: 'create:cogwheel',
		C: 'create:andesite_casing',
		I: 'create:whisk',
		R: 'cataclysm:coral_chunk'
	})

	event.remove({ output: 'create:encased_fan' })
	event.shaped('create:encased_fan', [
		'S ',
		'AR',
		'P '
	], {
		S: 'create:shaft',
		A: 'create:andesite_casing',
		P: 'create:propeller',
		R: 'cataclysm:amethyst_crab_shell'
	})

	// ================================================================
	// ACT VI - brass tier. Brass was 1 copper + 1 zinc -> 2 ingots.
	// Now 1:1 for 1, a flat 2x nerf inherited by every brass machine.
	// ================================================================
	event.remove({ id: 'create:mixing/brass_ingot' })
	event.recipes.create.mixing('create:brass_ingot', [
		'#forge:ingots/copper',
		'#forge:ingots/zinc'
	]).heated()

	// Electron tubes gate every smart/logistics block, and are consumed in
	// quantity -- so they draw on obelisk essence too.
	event.remove({ output: 'create:electron_tube' })
	event.shaped('create:electron_tube', [
		'LGL',
		'NON',
		'LGL'
	], {
		L: 'create:polished_rose_quartz',
		N: '#forge:plates/iron',
		G: '#forge:plates/gold',
		O: 'ancient_obelisks:ancient_greed'
	})

	// Precision mechanisms are the endgame Create material.
	event.remove({ output: 'create:precision_mechanism' })
	event.shaped('create:precision_mechanism', [
		'GRG',
		'CRC',
		'GCG'
	], {
		G: '#forge:plates/gold',
		C: 'create:cogwheel',
		R: 'dungeon_realm:general_relic'
	})

	// ================================================================
	// ACT VII - automation and logistics.
	// ================================================================
	// Deployer is the passive mob-farming enabler.
	event.remove({ output: 'create:deployer' })
	event.shaped('create:deployer', [
		'BX',
		'CR',
		'I '
	], {
		B: 'create:electron_tube',
		C: 'create:andesite_casing',
		I: 'create:brass_hand',
		R: 'cataclysm:void_core',
		X: 'dungeon_realm:general_relic'
	})

	// Storage Network root: was 4 cable + 4 quartz + 1 diamond for unlimited
	// networked storage. Now wants a boss drop and real diamond.
	event.remove({ output: 'storagenetwork:master' })
	event.shaped('storagenetwork:master', [
		'XkX',
		'kck',
		'XRd'
	], {
		k: 'storagenetwork:kabel',
		d: '#forge:gems/diamond',
		c: '#forge:storage_blocks/diamond',
		R: 'legendary_monsters:frozen_rune',
		X: 'dungeon_realm:general_relic'
	})

	// ================================================================
	// ACT VIII - machines that build machines.
	// ================================================================
	event.remove({ output: 'create:mechanical_crafter' })
	event.shaped('create:mechanical_crafter', [
		'BR',
		'CX',
		'T '
	], {
		B: 'create:electron_tube',
		C: 'create:brass_casing',
		T: 'minecraft:crafting_table',
		R: 'legendary_monsters:eye_crystal',
		X: 'dungeon_realm:general_relic'
	})

	event.remove({ output: 'extendedcrafting:basic_table' })
	event.shaped('extendedcrafting:basic_table', [
		'BAB',
		'CIC',
		'BSR'
	], {
		I: '#forge:storage_blocks/iron',
		C: 'minecraft:crafting_table',
		B: 'extendedcrafting:basic_component',
		S: 'extendedcrafting:black_iron_slate',
		A: 'extendedcrafting:basic_catalyst',
		R: 'born_in_chaos_v1:lifestealer_bone'
	})

	// The first fully automatic crafter: turns every downstream recipe from a
	// progression problem into a throughput problem.
	event.remove({ output: 'extendedcrafting:basic_auto_table' })
	event.shaped('extendedcrafting:basic_auto_table', [
		'PSP',
		'XTX',
		'XBX'
	], {
		T: 'extendedcrafting:basic_table',
		C: 'extendedcrafting:crystaltine_component',
		B: 'extendedcrafting:black_iron_ingot',
		S: 'extendedcrafting:redstone_component',
		P: 'legendary_monsters:portal_shard',
		X: 'dungeon_realm:general_relic'
	})

	// ================================================================
	// Ungateable by PMMO - these slot into GUIs and never fire a USE hook,
	// so cost is the only lever that reaches them.
	// ================================================================
	// Stack Upgrade Tier 1 cost 8 logs, ending storage scarcity before iron.
	event.remove({ output: 'sophisticatedstorage:stack_upgrade_tier_1' })
	event.shaped('sophisticatedstorage:stack_upgrade_tier_1', [
		'III',
		'IBI',
		'III'
	], {
		I: '#forge:storage_blocks/iron',
		B: 'sophisticatedstorage:upgrade_base'
	})

	// Magnet upgrades vacuum every drop in a radius with no pipes, no power and
	// no tech tier -- the worst passive-farming enabler in the pack.
	// replaceInput keeps the sophisticatedcore recipe type intact; rebuilding
	// these as plain shaped recipes would lose the upgrade-tier NBT carryover.
	event.replaceInput(
		{ output: 'sophisticatedbackpacks:magnet_upgrade' },
		'#forge:gems/lapis', 'cataclysm:void_core'
	)
	event.replaceInput(
		{ output: 'sophisticatedstorage:magnet_upgrade' },
		'#forge:gems/lapis', 'cataclysm:void_core'
	)

	// ================================================================
	// PIPEZ - gated BEHIND Create, not around it.
	//
	// Stock Pipez gave 16 pipes for 6 iron and a dropper, which made it
	// strictly better and vastly cheaper than Create's own logistics. Every
	// tier now consumes a Create component, so Pipez inherits the whole
	// casing -> obelisk-essence chain and can only be reached through Create.
	// ================================================================
	event.remove({ output: 'pipez:item_pipe' })
	event.shaped('8x pipez:item_pipe', [
		'III',
		'DCD',
		'III'
	], {
		I: '#forge:ingots/iron',
		D: 'minecraft:dropper',
		C: 'create:andesite_casing'
	})

	event.remove({ output: 'pipez:fluid_pipe' })
	event.shaped('8x pipez:fluid_pipe', [
		'III',
		'BCB',
		'III'
	], {
		I: '#forge:ingots/iron',
		B: 'minecraft:bucket',
		C: 'create:copper_casing'
	})

	event.remove({ output: 'pipez:energy_pipe' })
	event.shaped('8x pipez:energy_pipe', [
		'III',
		'BTB',
		'III'
	], {
		I: '#forge:ingots/iron',
		B: '#forge:storage_blocks/redstone',
		T: 'create:electron_tube'
	})

	event.remove({ output: 'pipez:universal_pipe' })
	event.shaped('4x pipez:universal_pipe', [
		'IEF',
		'MCM',
		'IEF'
	], {
		I: 'pipez:item_pipe',
		E: 'pipez:energy_pipe',
		F: 'pipez:fluid_pipe',
		M: '#forge:ingots/iron',
		C: 'create:brass_casing'
	})

	// Upgrade tiers: each wants a Create component of the matching tier.
	event.remove({ output: 'pipez:basic_upgrade' })
	event.shaped('pipez:basic_upgrade', [
		'INI',
		'NAN',
		'INI'
	], {
		N: '#forge:nuggets/iron',
		I: '#forge:ingots/iron',
		A: 'create:andesite_alloy'
	})

	event.remove({ output: 'pipez:improved_upgrade' })
	event.shaped('pipez:improved_upgrade', [
		'GRG',
		'RUR',
		'GTG'
	], {
		U: 'pipez:basic_upgrade',
		G: '#forge:ingots/gold',
		R: '#forge:dusts/redstone',
		T: 'create:electron_tube'
	})

	event.remove({ output: 'pipez:advanced_upgrade' })
	event.shaped('pipez:advanced_upgrade', [
		'CPC',
		'RUR',
		'CPC'
	], {
		C: 'cataclysm:chitin_claw',
		P: 'create:precision_mechanism',
		R: '#forge:storage_blocks/redstone',
		U: 'pipez:improved_upgrade'
	})

	event.remove({ output: 'pipez:ultimate_upgrade' })
	event.shaped('pipez:ultimate_upgrade', [
		'NMN',
		'PUP',
		'NMN'
	], {
		N: '#forge:ingots/netherite',
		M: 'alexsmobs:void_worm_mandible',
		P: 'create:precision_mechanism',
		U: 'pipez:advanced_upgrade'
	})
})
