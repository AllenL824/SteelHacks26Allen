"""Curated practice content. Kept as fixed text (not LLM-generated) so what a
learner sees is always correct. Selection is deterministic; Nemotron narrates."""

# Tongue twisters keyed by the leading sound they exercise.
TONGUE_TWISTERS: dict[str, list[str]] = {
    "s": ["She sells seashells by the seashore.",
          "Sally saw seven slippery snakes slide slowly south."],
    "sh": ["Sheila should share the shiny short shells she found."],
    "th": ["The thirty-three thankful thinkers thought it through."],
    "ch": ["Cheerful children chew chunky cherry chews."],
    "p": ["Peter Piper picked a peck of pickled peppers.",
          "Purple pandas prefer plump, perfectly ripe plums."],
    "b": ["Betty bought a bit of better butter to make her batter better."],
    "t": ["Ten tame tigers took tea together in town."],
    "d": ["Dizzy ducks dove down deep and darted about."],
    "k": ["How many cookies could a good cook cook?"],
    "c": ["Crisp crackers crackle and crunch in the crowded car."],
    "g": ["Great gray geese grazed gaily by the gate."],
    "f": ["Four fine fresh fish fried fast for Fred."],
    "v": ["Vivid vines vied for the very best view."],
    "r": ["Round the rugged rocks the ragged rascal ran."],
    "l": ["Larry loudly lulled the little lamb to sleep."],
    "m": ["Merry Mandy makes marvelous mellow music."],
    "n": ["Nine nimble noblemen nibbled by the nook."],
    "w": ["Which wristwatch is a Swiss wristwatch?"],
    "h": ["Harry hurried home hauling heavy hampers."],
    "j": ["Jolly jesters juggle jingling jars of jam."],
}

GENERAL_TWISTERS: list[str] = [
    "Red leather, yellow leather, red leather, yellow leather.",
    "A proper copper coffee pot.",
]

BREATHING: list[str] = [
    "Diaphragmatic breathing: inhale slowly through your nose for 4 counts and let "
    "your belly expand, then exhale gently for 6. Repeat 5 times before you read.",
    "Box breathing: in for 4, hold for 4, out for 4, hold for 4 — four rounds to settle your pace.",
]

# Passages (added under data/passages/) that are rich in a given sound.
PASSAGE_BY_SOUND: dict[str, str] = {
    "s": "sea_shore",
    "p": "pebble_path",
}


def pick_tongue_twister(sound: str | None) -> str:
    if sound and sound in TONGUE_TWISTERS:
        return TONGUE_TWISTERS[sound][0]
    return GENERAL_TWISTERS[0]


def pick_breathing() -> str:
    return BREATHING[0]


def suggest_passage(sound: str | None) -> str | None:
    if sound is None:
        return None
    return PASSAGE_BY_SOUND.get(sound)
