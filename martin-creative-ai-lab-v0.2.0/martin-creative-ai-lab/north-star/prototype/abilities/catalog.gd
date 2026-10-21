extends RefCounted
## Bounded original experimental profiles, never executable effects or class canon.
const PATH="res://abilities/catalog.json"
static func load_catalog(path:String=PATH) -> Dictionary:
	if not FileAccess.file_exists(path):return {"ok":false,"error":"Missing rush catalog","items":{}}
	var file=FileAccess.open(path,FileAccess.READ)
	if file==null or file.get_length()>16384:return {"ok":false,"error":"Unreadable or oversized rush catalog","items":{}}
	var parser=JSON.new()
	if parser.parse(file.get_as_text())!=OK:return {"ok":false,"error":"Invalid rush JSON","items":{}}
	return validate(parser.data)
static func validate(data:Variant) -> Dictionary:
	var failure={"ok":false,"error":"Invalid rush schema","items":{}}
	if not data is Dictionary or data.size()!=2 or not data.has_all(["schema_version","rushes"]):return failure
	if typeof(data.schema_version) not in [TYPE_INT,TYPE_FLOAT] or data.schema_version!=1:return failure
	if not data.rushes is Array or data.rushes.size()<1 or data.rushes.size()>2:return failure
	var items={}
	for row in data.rushes:
		if not row is Dictionary or row.size()!=7 or not row.has_all(["id","name","cost","speed","travel","recovery","cooldown"]):return failure
		if not row.id is String or row.id.length()<1 or row.id.length()>24 or row.id=="none" or items.has(row.id):return failure
		for index in row.id.length():
			var code=row.id.unicode_at(index)
			if not (code>=97 and code<=122 or index>0 and (code>=48 and code<=57 or code==95)):return failure
		if not row.name is String or row.name.length()<1 or row.name.length()>24:return failure
		for index in row.name.length():
			var code=row.name.unicode_at(index)
			if code<32 or code>126:return failure
		for key in ["cost","speed","travel","recovery","cooldown"]:
			if typeof(row[key]) not in [TYPE_INT,TYPE_FLOAT] or not is_finite(float(row[key])):return failure
		if row.cost!=floorf(row.cost) or row.cost<10 or row.cost>60 or row.speed<250 or row.speed>900:return failure
		if row.travel<0.10 or row.travel>0.40 or row.recovery<0.05 or row.recovery>0.80:return failure
		if row.cooldown<row.travel+row.recovery or row.cooldown>5:return failure
		items[row.id]=row.duplicate(true)
	return {"ok":true,"error":"","items":items}
