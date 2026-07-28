// Dungeon relics that gate the Create tree.
//
// WHY
// Create used to be gated by PMMO engineering levels, granted by quests that ran
// `/pmmo admin @p set engineering level N`. The level system was removed, that command no
// longer resolves, and the placement requirements it fed were a soft-lock. Create is now
// gated by exploration instead: three relics that only drop from dungeon chests
// (see kubejs/server_scripts/rpg_dungeon_loot.js).
//
// TEXTURES WITHOUT ART
// KubeJS looks for kubejs/assets/kubejs/textures/item/<name>.png and renders the missing
// texture checkerboard if it is absent. Rather than author PNGs, each item ships a model at
// kubejs/assets/kubejs/models/item/<name>.json that points layer0 at an existing Create
// texture. The item renders correctly with no new assets.
//
// RHINO: `var` only at this scope, and no const/let inside the callback - a repeated
// identifier across callbacks in one file throws "redeclaration of var" on the SECOND
// invocation, which has already cost five scripts in this pack.

var DUNGEON_RELICS = [
	{ id: 'rusted_gear', rarity: 'common' },
	{ id: 'brass_schematic', rarity: 'uncommon' },
	{ id: 'precision_core', rarity: 'rare' },
]

function registerRelics(event) {
	DUNGEON_RELICS.forEach(function (r) {
		event.create(r.id)
			.rarity(r.rarity)
			.maxStackSize(16)
			.fireResistant(true)        // dungeon chests burn; the gate should not be lost
	})
}

StartupEvents.registry('item', function (event) {
	registerRelics(event)
})
