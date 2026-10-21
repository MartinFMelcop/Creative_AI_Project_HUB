extends SceneTree
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()>1:printerr("Usage: godot --path <prototype> --script abilities/play.gd -- [candidate.json]");quit(2);return
	var view=load("res://abilities/view.gd").new()
	if args.size()==1:view.catalog_path=args[0]
	root.add_child.call_deferred(view)
