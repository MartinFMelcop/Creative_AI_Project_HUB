extends "../../north-star/prototype/tests/remote_journey.gd"
## Retained execution driver: actual C input selects a nondefault offered fitting.
func _process(delta:float) -> bool:
	if view!=null and view.remote.status=="preparing":
		for index in 3:tap(KEY_C)
	return super._process(delta)
