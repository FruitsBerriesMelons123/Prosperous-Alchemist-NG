# Prosperous Alchemist localization resources

Locale files are loaded at startup from the directory beside `alchemist.dll`:

```text
SKSE/Plugins/
├── alchemist.dll
└── locales/
	└── alchemist.zh-cn.json
```

Use a BCP 47 language tag in the filename. Tags are case-insensitive; examples include `alchemist.en.json`, `alchemist.es-419.json`, `alchemist.es-mx.json`, `alchemist.fr-ca.json`, `alchemist.pt.json`, `alchemist.zh-hk.json`, `alchemist.zh-cn.json`, `alchemist.zh-tw.json`, `alchemist.ja.json`, and `alchemist.ko.json`. The plugin also accepts an explicit `Language` value in the active `[Profile N]` in `alchemist.ini`; an empty value or `auto` follows the Windows user locale.

The bundled locale resources are Arabic (`ar`), Bulgarian (`bg`), Chinese Hong Kong (`zh-HK`), Chinese Simplified (`zh-CN`), Chinese Traditional (`zh-TW`), Croatian (`hr`), Czech (`cs`), Danish (`da`), Dutch (`nl`), English (`en`), Finnish (`fi`), French (`fr`), French Canada (`fr-CA`), German (`de`), Greek (`el`), Hebrew (`he`), Hindi (`hi`), Hungarian (`hu`), Indonesian (`id`), Italian (`it`), Japanese (`ja`), Korean (`ko`), Malay (`ms`), Norwegian Bokmål (`nb`), Polish (`pl`), Portuguese Brazil (`pt-BR`), Portuguese Europe (`pt`), Romanian (`ro`), Russian (`ru`), Slovak (`sk`), Spanish (`es`), Spanish Latin America (`es-419`), Spanish Mexico (`es-MX`), Swedish (`sv`), Tagalog (`tl`), Thai (`th`), Turkish (`tr`), Ukrainian (`uk`), and Vietnamese (`vi`).

The loader tries the English resource first, then the base language, then the exact selected tag. Missing keys, invalid values, malformed JSON, or unavailable fonts fall back without preventing the overlay from opening. Every bundled resource in this repository contains the complete English key set; custom resources may translate only the keys they need and use the English fallback for the rest.

The supported schema is UTF-8 JSON:

```json
{
  "locale": "fr",
  "languageName": "Français",
  "fonts": ["NotoSans-Regular.ttf"],
  "strings": {
	"ui.settings": "Paramètres"
  }
}
```

`strings` values are UTF-8 display strings. Format strings use named placeholders such as `{count}`, `{page}`, `{pages}`, `{phase}`, `{current}`, `{total}`, `{percent}`, `{reason}`, `{name}`, `{identity}`, `{profile}`, and `{profileName}`. Keep those placeholders when translating the corresponding message. The recipe search operators are provided by the single-token `search.operator.and` and `search.operator.or` values; keep `{and}` and `{or}` in `ui.searchSyntax` so the syntax help and parser use the same localized tokens. Every bundled resource includes the complete profile-name and profile-selection workflow; custom resources may omit keys and use the English fallback.

The built-in English fallback is authoritative for keys not present in a custom resource. User translations can be added or replaced without rebuilding the plugin; restart Skyrim after changing a resource.
