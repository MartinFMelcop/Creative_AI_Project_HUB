// New adaptation fiction. Commitments alter the afternoon handover, not past deliveries.
export class Handover {
  constructor(morning) {
    if(!morning.morning.ending)throw new Error('Finish the morning before the handover.');
    this.morning=structuredClone(morning);
    this.state={stage:'table',heard:[],order:morning.morning.record_corrected?'clear':'disputed',
      decision:null,term:null,ending:null};
    this.history=[];
  }
  snapshot(){return {handover:structuredClone(this.state),morning:structuredClone(this.morning)};}
  afternoon() {
    const s=this.morning.morning;
    const ferry=s.ferry&&this.state.decision!=='lend-ferry',iven=s.iven&&this.state.decision!=='send-guide';
    return {road:s.road,ferry,iven,route:s.road?'causeway':ferry?'ferry':'ridge trail',
      grain_per_trip:s.road?4:ferry?2:1,shifts_per_trip:s.road?1:ferry?(iven?1:2):2};
  }
  facts() {
    const s=this.morning.morning;
    return [`Morning record: ${s.people} of 4 mill villagers at the clinic; Iven ${s.iven?'present then':'still across the channel'}.`,
      s.medicine==='supplied'?`Clinic supplied ${s.timely?'on time':'late; morning callers must be recalled'}.`:s.medicine==='ready'?'Dry medicine on the steps; delivery still unfinished.':'Clinic still needs dry medicine.',
      `${s.grain} of 4 grain crates delivered. Seed ${s.seed==='sown'?'sown; harvest unknown':s.seed==='saved'?'dry in the yard':'still in the loft'}.`,
      s.reserve_used?'Depot reserve used; replacement outstanding.':'Depot reserve untouched.',
      this.state.order==='clear'?'Work recorded as the crossing crew’s request.':'Council authority disputed; the original false order remains visible.'];
  }
  opening() {
    const s=this.morning.morning;
    const lines=["The noon wagon has stopped outside the clinic. A courier climbs down with two boat hands and a length of red towline. His name is Dain. He looks past Mara's table toward the landing.",
      "'The upstream landing lost its boat,' he says. 'We're going to rig a crossing there. I need a vessel, or someone who knows this channel.' He puts a receipt beside the work list. 'This is a request. It isn't a council order.'",
      s.ferry?"The ready ferry is tied above the landing. One of Dain's boat hands walks down to look at it; Mara calls her back before she touches the rope.":"There is no ready ferry to hand over. Dain leaves the towline on the wagon. 'A hull you haven't made safe won't help us.'",
      "Mara turns the receipt sideways. 'Read the list first. If you take something, write what we have left.' Dain takes off his pack and sits. For the first time today, no one is waiting for you to carry a load."];
    if(!s.iven)lines.push("Iven's line is still open on the list. Dain draws his finger back from it. He cannot ask a stranded man to steer for another village.");
    if(s.people<4)lines.push("There are empty chairs beside the table. Mara sets the missing villagers' locations in front of Dain; she does not speak for them.");
    if(this.state.order==='disputed')lines.push("Dain stops at the words 'council order'. 'I didn't bring this.' Mara keeps her hand over the page so he cannot pull it away. The Keeper has stayed in the workshop.");
    return lines.join('\n\n');
  }
  choices() {
    const s=this.state,m=this.morning.morning,options=[];
    const add=(name,label,detail)=>options.push({name,label,detail,cost:0});
    if(s.ending)return options;
    if(s.stage==='table') {
      if(!s.heard.includes('list'))add('read-list','Read the deliveries and unfinished work aloud.','Keep clinic timing, people, food and seed separate.');
      if(!s.heard.includes('mara'))add('hear-mara','Ask Mara what she needs to keep.','Hear the local cost of lending transport or its boat hand.');
      if(m.iven&&!s.heard.includes('iven'))add('hear-iven','Let Iven answer the request for a guide.','Only Iven can offer his own afternoon.');
      if(m.people===4&&!s.heard.includes('senn'))add('hear-senn','Ask Senn about the seed and the next rain.','She is here because the whole mill party reached the yard.');
      if(m.record_corrected&&!s.heard.includes('keeper'))add('hear-keeper','Ask the Keeper about the road.','A repair is a fact; council authority is a separate claim.');
      if(s.order==='disputed')add('correct-order','Withdraw the false order in front of Dain.','Record the crossing crew’s responsibility here; keep the night conversation and morning list intact.');
      add('settle','Decide what leaves with the wagon.','The morning clock is finished. Speaking costs no shifts.');
    } else if(s.stage==='decision') {
      add('keep-crossing','Keep the village’s transport and crew here.','Dain receives no boat or guide today. Local work keeps its current capacity.');
      if(m.ferry)add('lend-ferry','Lend the ready ferry to Dain’s two boat hands.',(m.iven?'Iven stays here. ':'No local guide is sent. ')+(m.road?'Keep the causeway; lose the backup ferry until it returns.':'Lose the only fast local crossing. The ridge trail carries 1 crate per 2 shifts.'));
      if(s.heard.includes('iven'))add('send-guide','Accept Iven’s offer to guide the upstream crew.',m.road?'Keep the causeway and any local ferry; Iven leaves with the wagon.':m.ferry?'Keep the ferry here, but a loaded local trip without Iven takes 2 shifts instead of 1.':'Keep the ridge trail; Iven leaves with the wagon. No faster local crossing opens.');
      add('back-to-table','Return to the table before committing.','Hear anyone still present. Nothing has been handed over.');
    } else if(s.decision==='keep-crossing') {
      add('decline','Sign a refusal for this request.','No later loan is promised. Dain must find help elsewhere.');
      add('review-later','Leave the request open for a later crew.','No boat or guide goes now. A later review is a request, not a promised delivery.');
    } else {
      add('return-at-dusk','Write a return due at dusk.',s.decision==='lend-ferry'?'Dain accepts the ferry return deadline; the village depends on him meeting it.':'Iven agrees to guide one afternoon and return by dusk; Dain accepts that limit.');
      add('open-return','Allow the loan through the upstream recovery.',s.decision==='lend-ferry'?'No return time is promised. The local ferry stays unavailable until the upstream crew brings it back.':'Iven agrees to stay through the recovery. There is no promised return time.');
    }
    return options;
  }
  act(action) {
    const choice=this.choices().find(c=>c.name===action);if(!choice)throw new Error('That handover choice is unavailable.');
    const before=this.snapshot(),s=this.state,m=this.morning.morning;let text='';
    switch(action) {
      case 'read-list':s.heard.push('list');text="You read each line. Dain starts to write 'village supplied', then stops when Mara taps the clinic entry. He copies the entries separately.\n\n"+this.facts().join('\n\n');break;
      case 'hear-mara':
        s.heard.push('mara');
        text="Mara slides the receipt under the table leg to stop it rocking. 'When you say we're finished, someone goes home. That's why I want the loads counted.'\n\n";
        text+=m.grain<4?`'There are ${4-m.grain} grain crates left at the mill. The kitchen can't cook a receipt. If the ferry goes, tell the carrying crew before they walk down there.'`:"'The kitchens have their grain. That gives us room to help. It doesn't mean no one will need the river this afternoon.'";
        text+='\n\n'+(m.medicine==='missing'?"She glances toward the empty clinic shelf. 'Put dry medicine first. We still haven't brought any.'":m.medicine==='ready'?"She glances toward the clinic steps. 'Keep the dry supplies on this list until the attendant has them. A chest near a door isn't care.'":m.timely?"The attendant calls Mara from the doorway. Mara raises one finger, asking for a moment. 'We started the clinic on time. I'd like to keep it working.'":"'Those people left the morning queue,' she says. 'The afternoon crew has to find them again. Don't change the arrival time to spare me.'");
        break;
      case 'hear-iven':
        s.heard.push('iven');
        text="Iven lifts his boot from under the table and pours a little river water onto the step. 'Your boat hands know knots?' Dain says they do. 'Good. There's a bar above the old landing. A neat knot won't tell you where it is.'\n\nHe puts his boot back on. 'I'll show them. One afternoon, if you need me back; longer if this crew can spare me. Ask them first.'\n\nDain reaches for the receipt. Iven keeps two fingers on it. 'Write my name beside guide. Don't put me under cargo.'";
        if(!m.road&&m.ferry)text+="\n\nMara looks toward the ferry. 'That leaves us rowing alone.' Iven nods. He doesn't take the receipt from her.";
        break;
      case 'hear-senn':
        s.heard.push('senn');
        text=m.seed==='sown'?"Senn has soil beneath her nails. She takes a bent nail from her pocket and lays it beside the key. 'The strip is drained. The seed is in. Next rain, someone has to clear the mouth of that drain.'":"Senn draws the loft key toward herself. "+(m.seed==='saved'?"'My seed is dry in the yard. Dry is better than lost. It isn't the same as planted.'":"'My seed is still on the loft shelf. Don't let someone open it for the kitchens because the sack looks like food.'");
        text+="\n\nDain says his boat hands will make up the loan by working the fields here tomorrow. Senn looks at the two of them. 'Have you asked them?' One shakes her head. Dain crosses that offer off the receipt.\n\n'If they come, I'll find them work,' Senn says. 'But leave the loan under your name.' "+(m.seed==='sown'?"She leaves her chair to check the drain.":m.seed==='saved'?"She leaves her chair to check the sack in the yard.":"She checks the loft entry on the list.");break;
      case 'hear-keeper':
        s.heard.push('keeper');
        text=m.road?"The Keeper wipes the measuring cord with a rag. 'The cart crossed. That's what I can sign.' Dain asks how long the boards will hold. 'Test them after the water drops. I won't sign next winter from this chair.'":"The Keeper lays the cord alongside the table. 'There are still boards to fit. Don't write the road into your receipt as if we had fitted them.'";
        text+="\n\nMara asks whether the council should pay for the work. The Keeper looks at the work entry, then at you. 'Ask them. Keep the request under the names of the people who made it.' They fold the rag around the cord.";break;
      case 'correct-order':
        s.order='clear';
        text="You tell Dain that the council never gave the order you claimed at the workshop. He asks Mara to lift her hand. Under the old line you write 'requested by the crossing crew' and mark the withdrawal.\n\nMara leaves both lines readable. 'This belongs with the copy at the workshop,' she says. 'It doesn't repair that conversation.' Dain dates the correction. The Keeper is still in the workshop; no one adds their signature.";break;
      case 'settle':s.stage='decision';text=(s.heard.includes('mara')?"Dain pulls the receipt out from under the table leg. Mara replaces it with a wedge. ":"Dain takes the receipt from the table. ")+"'Now,' he says, 'which of these can I take?'\n\nThe boat hands wait by the towline. "+(s.heard.includes('iven')?"Iven has offered to guide them. He waits for the local crew's answer.":m.iven?"Iven is at the table. No one has asked him to leave.":"Iven remains across the channel. He is not part of this offer.");break;
      case 'back-to-table':s.stage='table';text="Dain sets the receipt down. 'Ask. The wagon can wait while we write this.' Mara keeps the work list open.";break;
      case 'keep-crossing':s.decision=action;s.stage='terms';text="You tell Dain that the village needs its transport and crew here. He coils the red towline. 'Then I go to the next landing.'\n\nMara holds out the receipt. 'Put refused, or put ask us again. Don't put promised.'";break;
      case 'lend-ferry':s.decision=action;s.stage='terms';text="Mara gives Dain the ferry line, but holds its last loop while he writes. His boat hands take the oars. "+(m.iven?"Iven stays with the village; lending a hull has not lent them its guide.":"The local crew has lent no one to steer it.")+"\n\n"+(m.road?"Mara points them past the causeway. 'We have that road. We won't have a second route while you're gone.'":"Mara calls to the carrying crew. 'Use the ridge trail. One crate, two shifts. The ferry is leaving.'")+"\n\nDain asks when the receipt should say the boat is due back.";break;
      case 'send-guide':s.decision=action;s.stage='terms';text="You accept Iven's offer. He picks up the bent mooring hook. "+(m.ferry?"He passes the ferry line to Mara. 'Show whoever takes the oars where the bow was patched.'":"'I'll bring this back,' he says, lifting the hook.")+"\n\n"+(m.road?(m.ferry?"Mara sets the line beside the causeway key. Both routes stay here.":"Mara keeps the causeway key. The cart route stays here."):m.ferry?"Mara calls to the local rower. Without Iven, each loaded ferry trip will take two shifts.":"Mara keeps the ridge trail on the list. Iven's leaving does not open a new local route.")+"\n\nIven puts a foot on the wagon step. 'One afternoon, or until their crossing is working?' Dain waits for the limit before signing.";break;
      default:
        s.term=action;s.stage='ended';s.ending=s.decision;
        text=action==='decline'?"Dain signs 'no boat or guide supplied'. Mara takes the local copy. He puts the towline back on the wagon and calls his crew."
          :action==='review-later'?"Dain writes 'ask the afternoon crew again'. Mara underlines that no loan has been agreed. The wagon leaves without a local boat or guide."
          :action==='return-at-dusk'?"Dain writes 'return due at dusk' and signs beside it. Mara keeps a copy. "+(s.decision==='send-guide'?"Iven reads the time before climbing onto the wagon.":"She lets go of the last loop. The boat hands lead the ferry upstream.")
          :"Dain writes 'return after the upstream recovery; no time agreed'. "+(s.decision==='send-guide'?"Iven reads it, signs his own name, and climbs onto the wagon.":"Mara lets go of the last loop. The boat hands lead the ferry upstream.");
    }
    const result={action,cost:0,text,before,after:this.snapshot()};this.history.push(result);return result;
  }
  epilogue() {
    if(!this.state.ending)throw new Error('The handover is still open.');
    const s=this.state,m=this.morning.morning,a=this.afternoon();
    const lines=[s.decision==='lend-ferry'?"The ferry rounds the upper bend with Dain's boat hands aboard. "+(m.iven?"Iven stays at the clinic yard. ":"")+"Mara pins the receipt over the empty ferry hook.":s.decision==='send-guide'?"The wagon takes Iven and his mooring hook upstream. The village keeps its own transport. Mara gives the remaining crew his instructions; Iven is no longer here to answer their questions.":"The wagon goes upstream without a local boat or guide. Mara leaves the local route and crew entries unchanged.",
      `Local afternoon route: ${a.route}. Grain capacity: ${a.grain_per_trip} crate(s) per ${a.shifts_per_trip} shift(s). The afternoon crew still has to move the outstanding loads.`,
      ...this.facts()];
    if(s.decision!=='keep-crossing')lines.push(s.term==='return-at-dusk'?"Mara leaves a space beside 'return due at dusk'. No one has returned yet. At dusk the next crew must check it, not tick it in advance.":"There is no return time on the receipt. The afternoon crew inherits that open loan along with its other work.");
    else lines.push(s.term==='review-later'?"Dain's request remains for the next crew to review. It is not a promised loan.":"This request has been refused. Dain must seek a vessel or guide elsewhere.");
    lines.push(m.people===4?"Mara counts the mill names once more before taking the list to the afternoon crew.":"Mara takes the missing names and their shelter locations to the afternoon crew. Dain's departure has not brought those people home.");
    return lines.join('\n\n');
  }
}
