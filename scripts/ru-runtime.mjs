import { SHIP_STRINGS_RU } from "./ship-strings.mjs";
import { SHIP_CATALOG_RU } from "./ship-catalog-strings.mjs";
import { SHIP_FAMILY_RU } from "./ship-family-strings.mjs";
import { MESSAGES_RU, MESSAGE_PATTERNS_RU } from "./message-strings.mjs";

const MODULE_ID = "lipatos-ocean";
const OCEAN_UI_SELECTOR = [
  '[class*="ocean-"]', '[class*="ocp-"]', '[class*="otcp-"]',
  '[class*="osw-"]', '[class*="otqs-"]', '[class*="oob-"]',
  '[class*="ship-refit"]', '[class*="ship-custom"]',
  '[class*="notification"]'
].join(", ");
const EXCLUDED = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "PRE", "OPTION"]);
const ATTRIBUTE_NAMES = ["title", "placeholder", "aria-label", "data-tooltip", "alt"];
const TRANSLATIONS = new Map(Object.entries({
  ...SHIP_STRINGS_RU,
  ...SHIP_CATALOG_RU,
  ...SHIP_FAMILY_RU,
  ...MESSAGES_RU
}));
const PATTERNS = MESSAGE_PATTERNS_RU.map(([source, replacement]) => [
  new RegExp(source, "u"), replacement
]);

function russianEnabled() {
  return typeof game !== "undefined" && String(game.i18n?.lang ?? "").toLowerCase().startsWith("ru");
}

/** Only exact known UI strings are changed. Never edit source data or user input. */
function translate(text) {
  if (typeof text !== "string" || !text.trim()) return text;
  const value = text.trim();
  let localized = TRANSLATIONS.get(value);
  if (!localized && value.startsWith("OCEAN.")) {
    const resolved = game.i18n.localize(value);
    if (resolved !== value) localized = resolved;
  }
  if (!localized) {
    for (const [pattern, replacement] of PATTERNS) {
      if (pattern.test(value)) {
        localized = value.replace(pattern, replacement);
        break;
      }
    }
  }
  if (!localized || localized === value) return text;
  return text.replace(value, localized);
}

function eligible(element) {
  return element && !EXCLUDED.has(element.tagName)
    && !element.closest('[contenteditable="true"]')
    && !!element.closest(OCEAN_UI_SELECTOR);
}

function translateElement(root) {
  if (!(root instanceof Element) || !russianEnabled()) return;
  if (!eligible(root) && !root.matches(OCEAN_UI_SELECTOR)) return;

  const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      return eligible(node.parentElement) && node.textContent?.trim()
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT;
    }
  });

  const nodes = [];
  for (let node = walk.nextNode(); node; node = walk.nextNode()) nodes.push(node);
  for (const node of nodes) {
    const next = translate(node.textContent);
    if (next !== node.textContent) node.textContent = next;
  }

  const elements = [root, ...root.querySelectorAll("*")];
  for (const element of elements) {
    if (!eligible(element)) continue;
    for (const attribute of ATTRIBUTE_NAMES) {
      if (!element.hasAttribute(attribute)) continue;
      const current = element.getAttribute(attribute);
      const next = translate(current);
      if (next !== current) element.setAttribute(attribute, next);
    }
    if (element instanceof HTMLInputElement && ["button", "submit", "reset"].includes(element.type)) {
      const next = translate(element.value);
      if (next !== element.value) element.value = next;
    }
  }
}

function translateAddedNode(node) {
  if (node.nodeType === Node.TEXT_NODE) {
    if (!eligible(node.parentElement)) return;
    const next = translate(node.textContent);
    if (next !== node.textContent) node.textContent = next;
    return;
  }
  if (!(node instanceof Element)) return;
  if (eligible(node) || node.matches(OCEAN_UI_SELECTOR)) {
    translateElement(node);
    return;
  }
  for (const root of node.querySelectorAll(OCEAN_UI_SELECTOR)) {
    if (!root.parentElement?.closest(OCEAN_UI_SELECTOR)) translateElement(root);
  }
}

async function applyI18nOverrides() {
  const response = await fetch(`modules/${MODULE_ID}/lang/ru.json`);
  if (!response.ok) throw new Error(`RU catalog HTTP ${response.status}`);
  const entries = await response.json();
  for (const [path, value] of Object.entries(entries)) {
    foundry.utils.setProperty(game.i18n.translations, path, value);
  }
  return Object.keys(entries).length;
}

Hooks.once("ready", async () => {
  if (!russianEnabled()) return;
  try {
    const count = await applyI18nOverrides();
    console.info(`${MODULE_ID} | Русская локализация Ocean: ${count} строк`);
  } catch (error) {
    console.error(`${MODULE_ID} | Не удалось загрузить русскую локализацию`, error);
  }

  for (const root of document.querySelectorAll(OCEAN_UI_SELECTOR)) {
    if (!root.parentElement?.closest(OCEAN_UI_SELECTOR)) translateElement(root);
  }

  const pending = new Set();
  let scheduled = false;
  const flush = () => {
    scheduled = false;
    const batch = [...pending];
    pending.clear();
    for (const node of batch) translateAddedNode(node);
  };
  const queue = node => {
    pending.add(node);
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(flush);
  };

  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === "characterData") {
        queue(record.target);
        continue;
      }
      for (const node of record.addedNodes) queue(node);
    }
  });
  observer.observe(document.body, { childList: true, characterData: true, subtree: true });

  const module = game.modules.get(MODULE_ID);
  if (module) module.api = { ...(module.api ?? {}), translate, count: TRANSLATIONS.size };
});
