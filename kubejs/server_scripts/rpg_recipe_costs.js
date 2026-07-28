// Tech recipe hardening. Create is SIDE-TECH, not part of the act spine.
//
// Three jobs:
//   1. Price the items PMMO cannot gate. Upgrades that slot into a GUI (magnets,
//      pipe upgrades, stack upgrades) never fire a USE hook, so cost is the only
//      lever that reaches them.
//   2. Harden the FOUNDATION. Andesite alloy, water wheels and casings were
//      near-free, which made every gate downstream of them shallow.
//   3. Make tech consume DUNGEON loot, so automation is paid for by raiding -
//      and so there is a standing reason to keep clearing dungeons.
//
// EVERY GATE HERE IS DUNGEON LOOT. NO MOD BOSS DROPS.
// This used to gate Create behind act-3/5/8 minibosses and, worst of all, the
// deployer behind cataclysm:void_core - whose Ender Golem now lives in act 9,
// past the Ender Dragon. Create was therefore unreachable until the final act
// while its own quest chapter claimed to be standalone. Three systems disagreeing.
//
// The gates are the three relics from kubejs/startup_scripts/rpg_dungeon_items.js,
// seeded into every dungeon chest table by rpg_dungeon_loot.js. Tiers match the
// Mühendislik chapter exactly, so recipe, quest and loot all say the same thing:
//   kubejs:rusted_gear       ~6%  andesite + copper casings, basic table
//   kubejs:brass_schematic   ~4%  brass casing, mixer, fan, electron tube
//   kubejs:precision_core    ~2%  precision mechanism, deployer, crafter, auto table

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
		O: 'kubejs:rusted_gear'
	})

	event.remove({ output: 'create:copper_casing' })
	event.shaped('2x create:copper_casing', [
		'LCL',
		'COC',
		'LCL'
	], {
		L: '#forge:stripped_logs',
		C: '#forge:ingots/copper',
		O: 'kubejs:rusted_gear'
	})

	event.remove({ output: 'create:brass_casing' })
	event.shaped('2x create:brass_casing', [
		'LBL',
		'BRB',
		'LBL'
	], {
		L: '#forge:stripped_logs',
		B: '#forge:ingots/brass',
		R: 'kubejs:brass_schematic'
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
		R: 'kubejs:brass_schematic'
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
		R: 'kubejs:brass_schematic'
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
		O: 'kubejs:brass_schematic'
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
		R: 'kubejs:precision_core'
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
		R: 'kubejs:precision_core',
		X: 'create:brass_sheet'
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
		R: 'kubejs:precision_core',
		X: 'create:brass_sheet'
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
		R: 'kubejs:rusted_gear'
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
		B: 'extendedcrafting:black_iron_ingot',
		S: 'extendedcrafting:redstone_component',
		P: 'kubejs:precision_core',
		X: 'create:brass_sheet'
	})

})
