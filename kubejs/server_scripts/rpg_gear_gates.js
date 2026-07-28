// Gate each armour set behind ITS OWN act's boss material.
//
// MEASURED ARMOUR (tools/gear_survey.py, player values):
//   diamond 20 | netherite 20 | cursium 30 | ignitium 32 | annihilator 33 |
//   dragonsteel 34 | ebonlord 45
//
// Most sets already gate correctly through the mods' own recipes:
//   ignitium    <- ignitium_ingot        (IGNIS, act 6)
//   dragonsteel <- dragonsteel_ingot     (fire dragon, act 7)
//   ebonlord    <- threat_tier_ultra tag (Threateningly Mobs bosses, act 8)
//
// Two did not. Both were gated behind ACT-8 drops while sitting at act-6/7 power,
// which made them dead options - strictly worse than ebonlord by the time you
// could build them:
//   cursium (30)     <- cursium_ingot   from MALEDICTUS   (act 8)
//   annihilator (33) <- portal_shard    from THE OBLITERATOR (act 8)
//
// Re-pointed at their own act's capstone drop. This also fixes the worst hole in
// the curve: diamond and netherite are BOTH 20 armour, so acts 3-5 were
// mechanically identical. Cursium at act 5 gives 20 -> 30 -> 32 -> 34 -> 45
// across acts 4-8 instead of a flat plateau then a jump.

const GATES = [
	// recipe id prefix,                    slots,                              new addition
	['cataclysm:smithing/cursium_',         ['helmet','chestplate','leggings','boots'],
	 'mowziesmobs:ice_crystal',             'cataclysm:cursium_upgrade_smithing_template'],
	['legendary_monsters:annihilator_',     ['helmet','chestplate','leggings','boots'],
	 'cataclysm:tidal_claws',               'legendary_monsters:annihilator_upgrade_smithing_template'],
]

function regate(event, prefix, slot, addition, template, result) {
	event.remove({ id: prefix + slot })
	event.custom({
		type: 'minecraft:smithing_transform',
		template: { item: template },
		base: { item: 'minecraft:netherite_' + slot },
		addition: { item: addition },
		result: { item: result },
	}).id('kubejs:gear_gate/' + result.replace(':', '/'))
}

ServerEvents.recipes(event => {
	let n = 0
	GATES.forEach(g => {
		const prefix = g[0], slots = g[1], addition = g[2], template = g[3]
		slots.forEach(slot => {
			const result = prefix.startsWith('cataclysm')
				? 'cataclysm:cursium_' + slot
				: 'legendary_monsters:annihilator_' + slot
			regate(event, prefix, slot, addition, template, result)
			n++
		})
	})
	console.info(`[rpg] re-gated ${n} armour pieces to their own act's boss drop`)
})
