extends SceneTree
## Explicit developer entry point; never changes the shipped main scene.
func _initialize() -> void:
	var args=OS.get_cmdline_user_args()
	if args.size()!=1 or not args[0].is_valid_int() or int(args[0])<1024 or int(args[0])>65535:
		printerr("Usage: godot --path <prototype> --script <authority/play.gd> -- <loopback-port>");quit(2);return
	var view=load(get_script().resource_path.get_base_dir()+"/view.gd").new()
	view.port=int(args[0]);root.add_child.call_deferred(view)
