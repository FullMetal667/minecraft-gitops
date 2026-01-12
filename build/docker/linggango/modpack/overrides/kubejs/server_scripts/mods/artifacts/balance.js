ServerEvents.loaded(e => {
  e.server.runCommandSilent("gamerule artifacts.vampiricGlove.maxHealingPerHit 2");
  e.server.runCommandSilent("gamerule artifacts.snorkel.isInfinite false");
  e.server.runCommandSilent('gamerule keepInventory true');
  e.server.runCommandSilent('gamerule artifacts.everlastingBeef.enabled false');
});
