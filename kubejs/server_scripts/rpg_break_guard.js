// Server-side validation of block-break speed.
//
// WHY
// Block breaking is client-driven: the client decides when a block is done and
// tells the server. Vanilla trusts that almost completely, so a client that lies
// (or a desynced/hacked one) mines instantly and the server accepts it. There is
// no anti-cheat mod in this pack, so nothing checks it today.
//
// HOW
// leftClicked fires when a player STARTS breaking a block. We stamp the time.
// broken fires when they finish. If the elapsed time is far below what the block
// hardness and the player's own dig speed allow, the break is cancelled - the
// server keeps the block and re-sends it, which snaps the client back.
//
// Vanilla break time: ticks = 1 / (digSpeed / hardness / 30) when the tool can
// harvest, /100 when it cannot. digSpeed already includes tool tier, Efficiency,
// Haste, Mining Fatigue, being underwater and off-ground, so a legitimately fast
// setup is fast HERE TOO and passes.
//
// DELIBERATELY CONSERVATIVE:
//  * TOLERANCE 0.45 - a break only fails if it took under 45% of the minimum, so
//    lag, rounding and a partially-mined block never trip it.
//  * Blocks with no recorded start are ALLOWED. AoE hammers, veinminers and
//    Apotheosis area-break send one leftClick and break many blocks; failing the
//    unclicked ones would break those tools completely.
//  * Instant-break blocks (hardness <= 0) are skipped entirely.
//  * Creative mode is skipped.

// RHINO SCOPING: `const`/`let` inside a repeatedly-invoked callback throws
// "redeclaration of var <name>" on the SECOND invocation. This guard shipped with
// `const p = event.player` in both handlers and threw on every break after the
// first - it failed open, so blocks broke normally and nothing looked wrong, while
// the guard policed exactly zero of them. Bodies live in named functions using
// `var` only. This is the fifth time this bug has bitten in this pack.

// TWO THRESHOLDS, because a false positive here is far worse than a missed cheat:
// cancelling a legitimate break makes the block UNBREAKABLE for that player. The
// client animates the break, the server refuses it, and the block snaps back - which
// is indistinguishable from a broken game. Seen live when this was mis-set.
//
//  REVERT_AT - only breaks under this fraction of the minimum are cancelled. At 0.10
//              the client claims a block fell in a tenth of its fastest possible time,
//              which no amount of lag or rounding produces.
//  LOG_AT    - suspicious but plausible; logged and ALLOWED, so real cheating shows up
//              in the log before anyone's mining is broken by it.
var REVERT_AT = 0.10
var LOG_AT = 0.45
var LOG_VIOLATIONS = true

// player uuid -> { key: "x,y,z", t: epoch millis }
var breakStart = {}

function posKey(pos) {
	return pos.x + ',' + pos.y + ',' + pos.z
}

// leftClicked fires EVERY TICK while the button is held, not once when mining
// starts - measured at 9 events in a single second on one block. Overwriting the
// timestamp each time leaves `t` one tick old when `broken` fires, so elapsed reads
// ~50ms instead of the real mining time and EVERY legitimate break looks illegal.
// Only the first click on a given position may set the clock; repeats keep it.
function stampBreakStart(event) {
	var p = event.player
	if (!p) return
	var id = String(p.uuid)
	var key = posKey(event.block.pos)
	var rec = breakStart[id]
	if (rec && rec.key === key) return        // already timing this block - do not reset
	breakStart[id] = { key: key, t: Date.now() }
}

function checkBreakSpeed(event) {
	var p = event.player
	if (!p || p.creative) return

	var block = event.block
	var state = block.blockState
	var pos = block.pos

	var hardness = state.getDestroySpeed(block.level, pos)
	if (!hardness || hardness <= 0) return           // instant-break, nothing to police

	var rec = breakStart[String(p.uuid)]
	if (!rec || rec.key !== posKey(pos)) return      // AoE / no recorded start - allow

	var dig = p.getDestroySpeed(state)                // includes tool, ench, haste
	if (!dig || dig <= 0) return

	var canHarvest = p.hasCorrectToolForDrops ? p.hasCorrectToolForDrops(state) : true
	var perTick = dig / hardness / (canHarvest ? 30.0 : 100.0)
	if (perTick >= 1.0) return                        // legitimately one-tick

	var minMillis = (1.0 / perTick) * 50.0            // ticks -> ms
	var elapsed = Date.now() - rec.t

	if (elapsed >= minMillis * LOG_AT) return          // normal play

	var what = state.getBlock().getDescriptionId()
	if (elapsed < minMillis * REVERT_AT) {
		event.cancel()
		if (LOG_VIOLATIONS) {
			console.warn('[break-guard] REVERTED ' + what + ' for ' + p.username
				+ ' - took ' + elapsed + 'ms, minimum ' + Math.round(minMillis) + 'ms')
		}
	} else if (LOG_VIOLATIONS) {
		console.info('[break-guard] suspicious (allowed) ' + what + ' for ' + p.username
			+ ' - took ' + elapsed + 'ms, minimum ' + Math.round(minMillis) + 'ms')
	}
}

BlockEvents.leftClicked(event => {
	try { stampBreakStart(event) }
	catch (e) { /* never let the guard break normal play */ }
})

BlockEvents.broken(event => {
	try { checkBreakSpeed(event) }
	catch (e) {
		// A guard that throws would cancel legitimate breaks. Fail open.
		console.error('[break-guard] error (failing open): ' + e)
	}
})
