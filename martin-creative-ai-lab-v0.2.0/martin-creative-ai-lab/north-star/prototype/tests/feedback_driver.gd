extends RefCounted
const Gate=preload("res://return_gate.gd")
const Combat=preload("res://combat.gd")
const GroundDriver=preload("res://tests/grounding_driver.gd")
var labels:Array[String]=[]
var failures:Array[String]=[]
func check(value:bool,label:String) -> void:
	labels.append(label)
	if not value:failures.append(label)
func arrival(role:String="Guardian",outfit:String="standard"):
	var g=Combat.new();g.reset(role);g.fit_outfit(outfit);g.hp=3;g.energy=44;g.courier.x=1000;g.mode="won";return g
func room(aid:String=""):
	var r=Gate.new();r.begin(arrival(),"available",aid);r.game.player=Gate.GROUND;return r
func hold(r,ticks:int=30) -> void:
	for tick in ticks:r.step(1.0/60,{"interact":true})
func run(scene,output:String) -> Dictionary:
	for role in ["Guardian","Duelist"]:
		for outfit in ["standard","riveted","trail","field_sash"]:
			for aid in ["","heal","brace"]:
				var source=arrival(role,outfit);var before:Dictionary=source.snapshot()
				var plan:Dictionary=Gate.preparation(source.hp,source.health_limit,aid)
				var line:String=Gate.preparation_line(source.hp,source.health_limit,aid)
				var r=Gate.new();r.begin(source,"available",aid)
				check(r.game.hp==plan.hp and r.game.cargo==plan.integrity,"Preview matches actual prepared resources: "+role+"/"+outfit+"/"+aid)
				check(source.snapshot()==before and line.contains("winch hit first"),"Preview is read-only and explains winch hit: "+outfit+"/"+aid)
	check(Gate.preparation(0,5,"").is_empty() and Gate.preparation(3,2,"").is_empty() and Gate.preparation(3,5,"invalid").is_empty(),"Invalid preparation cannot invent a plan")
	check(Gate.preparation(5,5,"heal").hp==5,"Preview health cannot exceed fitting limit")
	check(not Gate.preparation(3,5,"heal").ground_after_hit and Gate.preparation(3,5,"brace").ground_after_hit,"Heal cannot substitute for brace after winch damage")
	var r=room();hold(r)
	check(r.grounding_review.status=="working" and is_equal_approx(r.grounding_review.seconds,.5),"Review observes actual committed time")
	r.step(.01,{"move":Vector2.RIGHT,"interact":true})
	check(r.grounding_review.cause=="movement" and r.grounding_review.spent==0 and r.game.cargo==2,"Movement cancellation is distinct and free")
	r=room();hold(r);r.step(.01,{})
	check(r.grounding_review.cause=="release" and r.feedback_lines()[0].contains("Cost 0"),"Release is explained without charging")
	r=room();hold(r);r.suspend();r.game.mode="paused";var frozen:Dictionary=r.snapshot();hold(r)
	check(r.snapshot()==frozen and r.grounding_review.cause=="suspended","Suspension retains truthful review without hidden progress")
	r=room();r.progress=1.49;r.working=Gate.GROUND_INDEX;r.channel=true
	r.grounding_review={"status":"working","cause":"working","seconds":1.49,"start_integrity":2,"spent":0}
	r.game.phase="bolt";r.game.clock=.99;r.game.target=Gate.WINCH;r.step(.02,{"interact":true})
	check(r.grounding_review.cause=="winch hit" and r.grounding_review.spent==0 and r.grounding_review.integrity==1 and not r.grounded,"Same-frame winch interruption explains no cost paid")
	check(r.feedback_lines()[1].contains("grounding needs 2+") and r.feedback_lines()[1].contains("3 close counters"),"Blocked grounding offers existing alternatives")
	var review:Dictionary=r.snapshot();r.grounding_review.cause="changed"
	check(review.grounding_review.cause=="winch hit","Snapshot review is an independent copy")
	r=room();hold(r,20);r.game.phase="bolt";r.game.clock=.99;r.game.target=r.game.player;r.step(.02,{"interact":true})
	check(r.grounding_review.cause=="player hit" and r.game.cargo==2,"Personal damage is not falsely called winch damage")
	r=room("brace");hold(r,20);r.game.phase="bolt";r.game.clock=.99;r.game.target=Gate.WINCH;r.step(.02,{"interact":true})
	check(r.game.cargo==2 and r.feedback_lines()[1].contains("still available"),"Brace interruption explains remaining option")
	r.game.phase="rest";r.game.clock=0;hold(r,90)
	check(r.grounded and r.grounding_review.status=="completed" and r.grounding_review.start_integrity==2 and r.grounding_review.integrity==1 and r.grounding_review.spent==1,"Fresh completion records exact cost after earlier damage")
	check(r.feedback_lines()[0].contains("2 -> 1") and r.feedback_lines()[1].contains("both catches"),"Completion separates paid cost from remaining objective")
	r.suspend();check(r.grounding_review.status=="completed","Pausing cannot relabel successful completion")
	r.retry();check(r.grounding_review.is_empty() and r.game.cargo==3 and r.game.hp==3,"Retry clears review and restores immutable prepared arrival")
	r=room();hold(r,20);r.game.hp=0;r.step(.02,{"interact":true})
	check(r.game.mode=="lost" and r.grounding_review.cause=="player fell" and r.grounding_review.spent==0,"Terminal damage beats completion and remains attributed")
	check(r.feedback_lines()[1].contains("attempt is over") and not r.feedback_lines()[1].contains("still available"),"Terminal review offers retry instead of impossible live action")
	# The existing real-scene driver supplies eight complete connected journeys.
	var base:Dictionary=GroundDriver.new().run(scene,output+".grounding.json")
	for journey in base.journeys:
		var final:Dictionary=journey.return_gate.grounding_review
		check(final.status=="completed" and final.spent==1 and final.start_integrity-final.integrity==1,"Actual scene journey retains paid review: "+journey.role+"/"+journey.outfit)
	check(scene.return_gate.feedback_lines()[1].contains("passage is open"),"Successful review confirms completed objective instead of unfinished work")
	var hashes:Dictionary={}
	for name in ["arena.gd","return_gate.gd","tests/feedback_driver.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report:Dictionary={"schema_version":1,"checks":{"passed":labels.size()-failures.size(),"failed":failures.size()},
		"labels":labels,"failures":failures,"grounding_checks":base.checks,"journeys":base.journeys,"consumer_hashes":hashes}
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("FEEDBACK_CHECKS ",report.checks);return report
