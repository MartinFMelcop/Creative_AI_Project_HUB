extends SceneTree
## Read accepted PNGs; derive regions, foot pivots and scale without editing image bytes.
func _initialize() -> void:
	var actors := {}
	for actor in ["runner","warden"]:
		var filename: String="media/art/"+actor+"-motion.png"
		var image:=Image.load_from_file(ProjectSettings.globalize_path("res://"+filename))
		if image==null:
			push_error("Missing accepted atlas: "+filename)
			quit(1)
			return
		var frames: Array[Dictionary]=[]
		var max_height:=0
		for row in 4:
			for column in 4:
				var start:=Vector2i(roundi(column*image.get_width()/4.0),roundi(row*image.get_height()/4.0))
				var end:=Vector2i(roundi((column+1)*image.get_width()/4.0),roundi((row+1)*image.get_height()/4.0))
				var low:=end-start
				var high:=Vector2i(-1,-1)
				for y in range(start.y,end.y):
					for x in range(start.x,end.x):
						if image.get_pixel(x,y).a > 32.0/255.0:
							low=low.min(Vector2i(x,y)-start)
							high=high.max(Vector2i(x,y)-start)
				var gutter:=mini(mini(low.x,low.y),mini(end.x-start.x-high.x-1,end.y-start.y-high.y-1))
				if high.y<0 or gutter<2:
					push_error("Atlas cell is empty or crosses its border: %s %d"%[actor,row*4+column])
					quit(1)
					return
				var foot_sum:=0.0
				var foot_pixels:=0
				for y in range(maxi(low.y,high.y-12),high.y+1):
					for x in range(end.x-start.x):
						if image.get_pixel(start.x+x,start.y+y).a>32.0/255.0:
							foot_sum+=x
							foot_pixels+=1
				max_height=maxi(max_height,high.y-low.y+1)
				frames.append({"region":[start.x,start.y,end.x-start.x,end.y-start.y],
					"pivot":[snappedf(foot_sum/foot_pixels,.01),high.y+1],
					"opaque_bounds":[low.x,low.y,high.x+1,high.y+1]})
		actors[actor]={"texture":filename,"sha256":FileAccess.get_sha256("res://"+filename),
			"size":[image.get_width(),image.get_height()],"scale":snappedf((66.0 if actor=="runner" else 84.0)/max_height,.000001),"frames":frames}
	var output:=FileAccess.open("res://media/motion-catalog.json",FileAccess.WRITE)
	if output==null:
		push_error("Cannot write motion catalog.")
		quit(1)
		return
	output.store_string("{\n  \"version\": 1,\n  \"origin\": \"Accepted model-generated PNG bytes unchanged; native tools/build_motion_catalog.gd derives integration regions, foot pivots and scale.\",\n  \"actors\": {\n")
	for index in 2:
		var actor: String=["runner","warden"][index]
		var spec: Dictionary=actors[actor]
		output.store_string('    "'+actor+'": {\n')
		for key in ["texture","sha256","size","scale"]: output.store_string('      "'+key+'": '+JSON.stringify(spec[key])+',\n')
		output.store_string('      "frames": [\n')
		for n in 16: output.store_string('        '+JSON.stringify(spec.frames[n])+(',' if n<15 else '')+'\n')
		output.store_string('      ]\n    }'+(',' if index==0 else '')+'\n')
	output.store_string('  }\n}\n')
	output.close()
	print("MOTION_CATALOG 32 isolated frames; accepted PNG bytes unchanged")
	quit()
