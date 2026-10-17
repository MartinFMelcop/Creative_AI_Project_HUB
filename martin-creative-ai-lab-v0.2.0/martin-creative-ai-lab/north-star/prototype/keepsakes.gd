extends RefCounted
## Local, editable prototype continuity; this is not server authority or account data.
## The scene alone decides eligibility. earn() returns true only for a new known mark.
## Same-directory replacement protects prior bytes on ordinary write/rename failure;
## flush/readback do not establish power-loss durability or concurrent-writer safety.
const IDS := ["held_line", "drew_danger"]
const ROLES := {"Guardian":"held_line", "Duelist":"drew_danger"}
const MAX_BYTES := 4096
var earned: Array[String] = []
var equipped := ""
var dirty := false
var blocked := false
var status := "Session only. Earn a crossing mark to save."
var path := ""
var _selection_touched := false

func load_profile(profile_path: String) -> bool:
	path = profile_path
	earned.clear()
	equipped = ""
	dirty = false
	blocked = false
	_selection_touched = false
	var found := _read(path)
	if found.kind == "missing":
		status = "Session only. Earn a crossing mark to save."
		return true
	if found.kind != "valid":
		_block()
		return false
	_apply(found.data)
	status = "Saved locally."
	return true

func earn(role: String) -> bool:
	if not ROLES.has(role) or ROLES[role] in earned: return false
	var id: String = ROLES[role]
	earned.append(id)
	earned = _ordered(earned)
	dirty = true
	_save()
	return true

func cycle_equipped() -> String:
	var choices: Array[String] = [""]
	choices.append_array(earned)
	var next: String = choices[(choices.find(equipped) + 1) % choices.size()]
	_selection_touched = true
	if next != equipped:
		equipped = next
		dirty = true
		_save()
	return equipped

func retry_save() -> bool:
	if blocked:
		# Restored data supplies the selection; all known marks survive the repair.
		var found := _read(path)
		if found.kind not in ["valid", "missing"]:
			_block()
			return false
		var intended := equipped
		var known: Array[String] = earned.duplicate()
		var base: Dictionary = found.data if found.kind == "valid" else _empty()
		_apply(base)
		for id in known:
			if id not in earned: earned.append(id)
		earned = _ordered(earned)
		if _selection_touched: equipped = intended if intended in earned else ""
		blocked = false
		dirty = _payload() != base
		if not dirty:
			_selection_touched = false
			status = "Saved locally." if found.kind == "valid" else "Session only. Earn a crossing mark to save."
			return true
	if not dirty: return true
	return _save()

func snapshot() -> Dictionary:
	return {"earned":earned.duplicate(), "equipped":equipped, "dirty":dirty,
		"blocked":blocked, "status":status}

func _empty() -> Dictionary:
	return {"schema_version":1, "earned":[], "equipped":""}

func _payload() -> Dictionary:
	return {"schema_version":1, "earned":earned.duplicate(), "equipped":equipped}

func _ordered(values: Array) -> Array[String]:
	var result: Array[String] = []
	for id in IDS:
		if id in values: result.append(id)
	return result

func _apply(data: Dictionary) -> void:
	earned = _ordered(data.earned)
	equipped = data.equipped

func _valid(value: Variant) -> bool:
	if not value is Dictionary or value.size() != 3: return false
	for key in ["schema_version", "earned", "equipped"]:
		if not value.has(key): return false
	if typeof(value.schema_version) not in [TYPE_INT, TYPE_FLOAT] or value.schema_version != 1: return false
	if not value.earned is Array or value.earned.size() > IDS.size(): return false
	var seen: Array[String] = []
	for id in value.earned:
		if not id is String or id not in IDS or id in seen: return false
		seen.append(id)
	return value.equipped is String and (value.equipped == "" or value.equipped in seen)

func _read(candidate: String) -> Dictionary:
	if candidate.is_empty(): return {"kind":"invalid"}
	if not FileAccess.file_exists(candidate):
		return {"kind":"invalid"} if DirAccess.dir_exists_absolute(candidate) else {"kind":"missing"}
	var file := FileAccess.open(candidate, FileAccess.READ)
	if file == null: return {"kind":"invalid"}
	var length := file.get_length()
	if length > MAX_BYTES:
		file.close()
		return {"kind":"invalid"}
	var bytes := file.get_buffer(length)
	file.close()
	if bytes.size() != length: return {"kind":"invalid"}
	var content := bytes.get_string_from_utf8()
	if content.to_utf8_buffer() != bytes: return {"kind":"invalid"}
	var parser := JSON.new()
	if parser.parse(content) != OK or not _valid(parser.data): return {"kind":"invalid"}
	var normalized: Dictionary = {"schema_version":1, "earned":_ordered(parser.data.earned), "equipped":parser.data.equipped}
	return {"kind":"valid", "data":normalized}

func _block() -> void:
	blocked = true
	status = "Profile unavailable. Restore or remove it, then F5; session marks remain."

func _save() -> bool:
	if blocked:
		_block()
		return false
	# Unknown primary bytes must not be replaced, even if changed after initial load.
	var primary := _read(path)
	if primary.kind not in ["valid", "missing"]:
		_block()
		return false
	var temporary := path + "." + str(OS.get_process_id()) + "." + str(Time.get_ticks_usec()) + ".tmp"
	if FileAccess.file_exists(temporary): return _write_failed()
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null: return _write_failed()
	file.store_string(JSON.stringify(_payload()) + "\n")
	file.flush()
	var write_error := file.get_error()
	file.close()
	var checked := _read(temporary)
	if write_error != OK or checked.kind != "valid" or checked.data != _payload():
		DirAccess.remove_absolute(temporary)
		return _write_failed()
	if _replace_file(temporary, path) != OK:
		DirAccess.remove_absolute(temporary)
		return _write_failed()
	dirty = false
	_selection_touched = false
	status = "Saved locally."
	return true

func _replace_file(from: String, to: String) -> Error:
	return DirAccess.rename_absolute(from, to)

func _write_failed() -> bool:
	dirty = true
	status = "Not saved. Session marks remain; F5 retries."
	return false
