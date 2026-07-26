// Enforceable Mine and Slash progression tasks for FTB Quests.
//
// MnS ships no advancements, and FTB Quests has no native way to read a
// character level -- so these are `custom` tasks whose check reads MnS's own
// player data directly. Nothing here is self-reported.
//
// API, all confirmed from bytecode:
//   Load.Unit(entity)            -> EntityData
//   EntityData.getLevel()        -> int
//   Load.player(player)          -> PlayerData
//   PlayerData.statPoints        -> StatPointsData
//   event.setCheck((data, player) => ...)   data.setProgress(1) completes it
//
// Tasks bind by their 16-hex task id in the chapter .snbt.

const Load = Java.loadClass('com.robertx22.mine_and_slash.uncommon.datasaving.Load')

// taskId -> required MnS character level
const LEVEL_TASKS = {
	'3000000000000C01': 5,
	'3000000000000C02': 10,
	'3000000000000C03': 20,
	'3000000000000C04': 30,
	'3000000000000C05': 45,
	'3000000000000C06': 60,
}

Object.keys(LEVEL_TASKS).forEach(taskId => {
	const required = LEVEL_TASKS[taskId]
	FTBQuestsEvents.customTask(taskId, event => {
		event.setMaxProgress(1)
		event.setCheckTimer(40)
		event.setCheck((data, player) => {
			try {
				if (Load.Unit(player).getLevel() >= required) {
					data.setProgress(1)
				}
			} catch (err) {
				// MnS data not loaded yet for this player; try again next tick
			}
		})
	})
})

// Total allocated core stat points, read from MnS player data.
// taskId -> required total spent points
const STAT_TASKS = {
	'3000000000000C11': 25,
	'3000000000000C12': 60,
	'3000000000000C13': 120,
}

Object.keys(STAT_TASKS).forEach(taskId => {
	const required = STAT_TASKS[taskId]
	FTBQuestsEvents.customTask(taskId, event => {
		event.setMaxProgress(1)
		event.setCheckTimer(40)
		event.setCheck((data, player) => {
			try {
				// StatPointsData.getAllocatedPoints() -> int (confirmed from bytecode)
				if (Load.player(player).statPoints.getAllocatedPoints() >= required) {
					data.setProgress(1)
				}
			} catch (err) {
				// MnS data not loaded yet for this player; try again next tick
			}
		})
	})
})
