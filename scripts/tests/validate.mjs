import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { SHIP_STRINGS_RU } from "../ship-strings.mjs";
import { SHIP_CATALOG_RU } from "../ship-catalog-strings.mjs";
import { SHIP_FAMILY_RU } from "../ship-family-strings.mjs";
import { MESSAGES_RU, MESSAGE_PATTERNS_RU } from "../message-strings.mjs";

const manifest = JSON.parse(readFileSync("module.json", "utf8"));
const catalog = JSON.parse(readFileSync("lang/ru.json", "utf8"));
assert.equal(manifest.id, "lipatos-ocean");
assert.equal(manifest.languages.find(x => x.lang === "ru")?.path, "lang/ru.json");
assert.equal(manifest.relationships.requires.some(x => x.id === "ocean"), true);

assert.equal(Object.keys(catalog).length, 619, "All 619 upstream Ocean localization entries must be present");
for (const [key, value] of Object.entries(catalog)) {
  assert.ok(key.startsWith("OCEAN."), `Invalid localization key: ${key}`);
  assert.equal(typeof value, "string");
  assert.ok(value.trim(), `Empty translation: ${key}`);
  assert.ok(/\p{Script=Cyrillic}/u.test(value) || key.endsWith(".filename"),
    `Non-Russian translation: ${key}`);
}
for (const key of [
  "OCEAN.travel.startFailed", "OCEAN.travel.shipFailed",
  "OCEAN.travel.presetSaveFailed", "OCEAN.travel.presetDeleteFailed",
  "OCEAN.settings.travelQuality.saveFailed", "OCEAN.travel.saveFailed"
]) assert.ok(catalog[key].includes("{message}"), `Missing message placeholder: ${key}`);
for (const key of [
  "OCEAN.travel.convertedFullscreen", "OCEAN.travel.convertedCanvasBackground",
  "OCEAN.travel.restored"
]) assert.ok(catalog[key].includes("{name}"), `Missing scene-name placeholder: ${key}`);

const knownStrings = Object.assign({}, SHIP_STRINGS_RU, SHIP_CATALOG_RU, SHIP_FAMILY_RU, MESSAGES_RU);
assert.equal(Object.keys(knownStrings).length, 494, "All hard-coded UI replacements must be included");
for (const [key, value] of Object.entries(knownStrings)) {
  assert.ok(key.trim() && value.trim(), "Empty hard-coded replacement");
  assert.ok(/\p{Script=Cyrillic}/u.test(value), `Non-Russian UI replacement: ${key}`);
}
assert.ok(MESSAGE_PATTERNS_RU.every(x => x.length === 2));
console.log(`PASS: ${Object.keys(catalog).length} RU keys, ${Object.keys(knownStrings).length} hard-coded strings, ${MESSAGE_PATTERNS_RU.length} message patterns`);
