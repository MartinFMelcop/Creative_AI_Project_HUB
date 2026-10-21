extends RefCounted
## One bounded authoring contract shared by the live consumer and authoring tool.
const PATH := "res://data/fittings.json"
const FIELDS := ["id", "name", "health", "movement", "recovery", "visual", "station"]
const VISUALS := ["plain", "plates", "strips", "sash"]
const MAX_BYTES := 16384

static func number(value: Variant, minimum: float, maximum: float, integer: bool=false) -> bool:
	if typeof(value) not in [TYPE_INT, TYPE_FLOAT]: return false
	return is_finite(value) and value >= minimum and value <= maximum and (not integer or value == floor(value))

static func plain_text(value: Variant, maximum: int) -> bool:
	if not value is String or value.is_empty() or value.length() > maximum: return false
	for character in value:
		if character.unicode_at(0) < 32 or character.unicode_at(0) > 126: return false
	return value == value.strip_edges()

static func validate(data: Variant) -> Dictionary:
	var errors: Array[String] = []
	var items := {}
	if not data is Dictionary or data.size() != 2 or not data.has("schema_version") or not data.has("fittings"):
		return {"ok":false, "items":{}, "errors":["Expected exactly schema_version and fittings."]}
	if not number(data.schema_version, 1, 1, true): errors.append("Unsupported schema_version.")
	if not data.fittings is Array or data.fittings.size() < 2 or data.fittings.size() > 4:
		return {"ok":false, "items":{}, "errors":["The current room requires standard clothing and one to three benches."]}
	var stations: Array[Vector2] = []
	var id_pattern := RegEx.new()
	id_pattern.compile("^[a-z][a-z0-9_]{0,23}$")
	for index in data.fittings.size():
		var row: Variant = data.fittings[index]
		var label := "fittings[%d]" % index
		if not row is Dictionary or row.size() != FIELDS.size():
			errors.append(label + ": expected exactly " + str(FIELDS)); continue
		var complete := true
		for field in FIELDS:
			if not row.has(field): complete=false
		if not complete: errors.append(label + ": missing or unknown fields."); continue
		var initial_errors := errors.size()
		var valid_id: bool = row.id is String and id_pattern.search(row.id) != null
		if not valid_id: errors.append(label + ": invalid id.")
		elif items.has(row.id): errors.append(label + ": duplicate id " + row.id)
		if not plain_text(row.name, 22): errors.append(label + ": name must be 1-22 printable ASCII characters.")
		if not number(row.health, 3, 7, true): errors.append(label + ": health must be an integer from 3 to 7.")
		if not number(row.movement, 0.6, 1.3): errors.append(label + ": movement must be from 0.6 to 1.3.")
		if not number(row.recovery, 10, 30): errors.append(label + ": recovery must be from 10 to 30 per second.")
		if not row.visual is String or row.visual not in VISUALS: errors.append(label + ": unknown visual.")
		if errors.size() != initial_errors: continue
		if row.id == "standard":
			if row.station != null or row.health != 5 or row.movement != 1.0 or row.recovery != 18.0 or row.visual != "plain":
				errors.append(label + ": standard must retain the original unfitted baseline and have no bench.")
		elif not row.station is Array or row.station.size() != 2:
			errors.append(label + ": station must contain x and y.")
		elif not number(row.station[0], 220, 930) or not number(row.station[1], 390, 470):
			errors.append(label + ": station is outside the usable room.")
		else:
			var at := Vector2(row.station[0], row.station[1])
			for previous in stations:
				if at.distance_to(previous) < 220: errors.append(label + ": benches and labels must be at least 220px apart.")
			stations.append(at)
		if valid_id: items[row.id] = row.duplicate(true)
	if not items.has("standard"): errors.append("Missing standard clothing.")
	return {"ok":errors.is_empty(), "items":items if errors.is_empty() else {}, "errors":errors}

static func load_catalog(path: String=PATH) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null: return {"ok":false, "items":{}, "errors":["Cannot read fitting catalog."]}
	if file.get_length() > MAX_BYTES:
		return {"ok":false, "items":{}, "errors":["Fitting catalog exceeds 16384 bytes."]}
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK:
		return {"ok":false, "items":{}, "errors":["Invalid fitting JSON at line %d: %s" % [parser.get_error_line(), parser.get_error_message()]]}
	return validate(parser.data)

static func visual(items: Dictionary, id: String) -> String:
	return items.get(id, {}).get("visual", "plain")
