// Death-penalty integrity.
//
// HQM hardcore mode gives every player a limited number of lives, so losing your
// inventory on death is the core stake of the pack. The Everlasting Upgrade makes a
// worn backpack survive death outright, which removes that stake for anyone who
// crafts one. The item stays registered (nothing else references it), it just can
// no longer be obtained in survival.

ServerEvents.recipes(event => {
	event.remove({ output: 'sophisticatedbackpacks:everlasting_upgrade' })
})
