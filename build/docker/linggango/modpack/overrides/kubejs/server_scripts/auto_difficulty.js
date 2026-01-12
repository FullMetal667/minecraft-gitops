ServerEvents.loaded(e => {
  e.server.runCommandSilent("difficulty hard");
  e.server.runCommandSilent("chillingHorrorEvent true")
});
