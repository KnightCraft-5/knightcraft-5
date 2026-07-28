// Remove damage invulnerability frames from mobs.
//
// WHY
// Vanilla LivingEntity.hurt() sets invulnerableTime = 20 on every hit, and for
// the first 10 ticks a further attack only applies (amount - lastHurt). Against
// a single target that caps total incoming damage at roughly one full hit per
// 0.5s REGARDLESS OF HOW MANY PLAYERS ARE ATTACKING - everyone after the first
// contributes only the difference, which is ~0 when the group has similar gear.
//
// That makes group boss fights nonsense: nine players deal barely more than one.
// It is also why melee attack speed above ~2/sec is wasted, and why multi-hit
// and AoE effects appear to do nothing to a single target.
//
// Players are deliberately NOT touched. Removing player i-frames would let a
// fast-attacking mob land its whole combo inside a tick and delete anyone.

EntityEvents.hurt(event => {
	const entity = event.entity
	if (!entity || entity.player) {
		return
	}
	// hurt() sets invulnerableTime = 20 BEFORE calling actuallyHurt(), which is
	// what fires this event - so clearing it here sticks, and the next attacker
	// lands a full hit instead of only their damage above the previous one.
	entity.invulnerableTime = 0
})
