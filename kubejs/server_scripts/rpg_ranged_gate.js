// Gate ranged damage by AMMO rather than by nerfing the bow into uselessness.
//
// WHY
// Ice and Fire's dragonbone arrow has a HARDCODED base damage of 10.0 against
// vanilla's 2.0 - five times, before any enchant or gem, and not configurable.
// Measured in game: dragonbone bow ~60 per shot against melee's ~37, so ranged
// was matching or beating melee despite melee carrying all the positional risk.
//
// Rather than gut Power and the ranged gems until the bow is worthless, the
// damage stays and the SUSTAIN goes: arrows become expensive, and Infinity can
// no longer sidestep that on dragon-related bows.
ServerEvents.recipes(event => {
	// 1 dragonbone + 1 wither shard used to give FIVE arrows. Wither shards come
	// from a dragon skeleton; five shots per bone made ammo effectively free.
	event.remove({ id: 'iceandfire:dragonbone_arrow' })
	event.shapeless('1x iceandfire:dragonbone_arrow',
		['iceandfire:dragonbone', 'iceandfire:wither_shard'])
		.id('kubejs:dragonbone_arrow')
})

// Infinity would make the ammo gate meaningless on the strongest bow in the pack.
// Stripped on a slow server tick: vanilla 1.20.1 has no per-item enchant gate,
// and an anvil could re-apply it anyway.
//
// TWO KUBEJS TRAPS THIS WORKS AROUND
//  1. PlayerEvents.tick does NOT exist in KubeJS 2001. It registers without error
//     and never fires. ServerEvents.tick + iterating players is the working form.
//  2. `const`/`let` inside a repeatedly-invoked callback throws
//     "redeclaration of var" under Rhino on the SECOND invocation - the same bug
//     that collapsed the gem upgrade loop. Everything below uses `var`.
var NO_INFINITY = ['iceandfire:dragonbone_bow']
var rangedTick = 0

function stripInfinity(player) {
	var inv = player.inventory
	var n = inv.getSlots ? inv.getSlots() : inv.size
	var i, stack, nbt, list, j, removed
	for (i = 0; i < n; i++) {
		stack = inv.getStackInSlot(i)
		if (!stack || stack.isEmpty()) continue
		if (NO_INFINITY.indexOf(String(stack.getId())) < 0) continue
		nbt = stack.getNbt()
		if (!nbt || !nbt.contains('Enchantments')) continue
		list = nbt.getList('Enchantments', 10)
		removed = false
		for (j = list.size() - 1; j >= 0; j--) {
			if (String(list.getCompound(j).getString('id')) === 'minecraft:infinity') {
				list.remove(j)
				removed = true
			}
		}
		if (removed) {
			player.tell(Text.red('Infinity does not hold on dragon-forged bows.'))
			console.info('[ranged] stripped Infinity from a dragonbone bow')
		}
	}
}

ServerEvents.tick(event => {
	rangedTick++
	if (rangedTick % 40 !== 0) return
	try {
		event.server.getPlayers().forEach(p => stripInfinity(p))
	} catch (e) {
		console.error('[ranged] ' + e)
	}
})
