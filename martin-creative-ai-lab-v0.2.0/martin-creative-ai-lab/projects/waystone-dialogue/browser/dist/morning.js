// New adaptation fiction. Morning work is separate from the unchanged flood rules.
export class Morning {
  constructor(night) {
    if(!night.expedition.ending)throw new Error('Finish the night crossing first.');
    this.night=structuredClone(night);
    const n=night.expedition,w=night.workshop;
    this.state={time:6,elapsed:0,people:n.saved,iven:n.iven==='rescued',
      road:n.bridge==='stable',ferry:n.route==='ferry'&&n.hull>0&&n.iven==='rescued',
      timber:1+Number(n.kit.includes('timber')),medicine:n.medicine==='delivered'?'supplied':'missing',reserve_used:false,
      timely:n.medicine==='delivered',grain:0,seed:'loft',record_corrected:!w.apology_due,ending:null};
    this.history=[];
  }
  snapshot(){return {morning:structuredClone(this.state),night:structuredClone(this.night)};}
  opening() {
    const n=this.night.expedition,s=this.state,w=this.night.workshop;
    const lines=["Mara has spread the crossing list on the clinic table. The paper has dried in ridges. Beside it lie six work counters and a key to the mill loft. A fresh timber bundle waits on the work cart, beside any equipment left from last night.",
      s.people===4?"All four villagers are here. Lio lifts a broken chair off the table; Senn asks for the loft key.":`${4-s.people} villagers are still across the channel. Mara leaves their names uncrossed. 'We know where they sheltered. Someone has to go.'`,
      s.medicine==='supplied'?"The night attendant passes with a bowl of clean dressings. The chest you delivered is open on her shelf.":n.medicine==='spoiled'?"The attendant has laid the ruined packets out to dry. She points to the clean shelf. 'The depot has replacements. Bring them before the third shift ends.'":"The clinic shelf is empty. The attendant needs the chest at the mill, or a replacement from the depot, before the third shift ends.",
      s.road?"The causeway took no new damage overnight. A cart can cross it. Mara sets a wheel chock beside the key.":s.ferry?"Iven has kept the ferry tied above the landing. 'Two grain crates a load,' he says. 'I'm not putting four on that bow.'":"The river has fallen below the ridge trail. It is slow, but passable on foot. The causeway still needs boards; the ferry must be readied before it carries loads.",
      "Four dry grain crates remain in the mill loft. The kitchens need all four by noon. The sowing seed is there too. Senn knows the drainage strips; bring the whole mill party back before her planting crew can work. The supply wagon leaves after six shifts."];
    if(!s.record_corrected)lines.push("The Keeper stops at the door. 'Mara, I need the council order corrected on this list before I put my name to another repair.' They do not reach for the measuring cord.");
    else if(w.flags.includes('FLAG_PLAYER_LIED'))lines.push("The Keeper puts a measuring cord beside the list. 'The order was withdrawn. Write the work down as village work.'");
    return lines.join('\n\n');
  }
  transport(){return this.state.road?'road':this.state.ferry?'ferry':'ridge';}
  choices() {
    const s=this.state,n=this.night.expedition,options=[];
    const add=(name,label,cost,detail)=>{if(cost<=s.time)options.push({name,label,cost,detail});};
    if(s.ending)return options;
    if(!s.record_corrected)add('correct-record','Correct the false council order on the public list.',1,'The Keeper will help measure the repair; the original night conversation remains on record.');
    if(!s.road&&s.timber&&s.record_corrected) {
      const cost=this.night.expedition.light?2:3;
      add('repair-road','Build a cart-bearing causeway.',cost,'Consume 1 timber bundle. Permanent road: 4 grain crates per shift; retrieval takes 1 shift.');
    }
    if(!s.ferry&&n.hull>0&&(n.hull>=3||s.timber))add('ready-ferry','Recover and ready the ferry.',2,`${n.hull<3?'Consume 1 timber bundle to patch the bow. ':''}2 grain crates per trip; Iven takes 1 shift, alone you take 2.`);
    if(s.people<4||!s.iven) {
      const cost=s.road?1:s.ferry?(s.iven?1:2):3;
      add('recover-crew','Bring the stranded villagers and Iven to the clinic yard.',cost,`Use the ${this.transport()}. ${4-s.people} villagers and ${s.iven?'no additional boat hand':'Iven'} to recover; Iven can steer later loads.`);
    }
    if(s.medicine==='missing') {
      if(['waiting','aboard'].includes(n.medicine))add('retrieve-chest','Retrieve the dry chest left at the mill.',s.road||s.ferry?1:2,`Use the ${this.transport()}; preserves the depot's reserve. Delivery to the clinic takes another shift.`);
      else add('depot','Collect replacement medicine from the high-road depot.',2,'Use the depot reserve. Delivery takes another shift; the clinic needs it by the end of shift 3.');
    }
    if(s.medicine==='ready')add('supply-clinic','Deliver the medicine and help the attendant set up.',1,`Complete at shift ${s.elapsed+1}: ${s.elapsed+1<=3?'morning care can start on time':'the clinic will open for afternoon care'}.`);
    if(s.grain<4) {
      const amount=s.road?4:s.ferry?2:1,cost=s.road?1:s.ferry?(s.iven?1:2):2;
      add('grain',`Bring ${Math.min(4-s.grain,amount)} grain crate(s) to the kitchens.`,cost,`Use the ${this.transport()}. ${s.grain}/4 delivered; only actual delivered crates count.`);
    }
    if(s.seed==='loft')add('seed','Retrieve the sowing seed from the loft.',s.road?1:s.ferry?(s.iven?1:2):2,`Use the ${this.transport()}. This load is separate from food; draining a planting strip takes 2 more shifts.`);
    if(s.seed==='saved'&&s.people===4)add('plant','Drain a strip and sow the recovered seed.',2,'Senn and the mill party can work the strip. Otherwise keep the seed dry for the next crew.');
    add('close','Hand over the remaining work and end the morning.',0,'Keep actual deliveries and a concrete afternoon work list.');
    return options;
  }
  act(action) {
    const choice=this.choices().find(c=>c.name===action);if(!choice)throw new Error('That morning choice is unavailable.');
    const before=this.snapshot(),s=this.state,n=this.night.expedition;let text='';
    switch(action) {
      case 'correct-record':s.record_corrected=true;text="You strike out 'council order' and write your own name beside the request. Mara keeps the old line legible. The Keeper checks it, then takes the measuring cord. 'Mark both piers. I'll call the lengths.'";break;
      case 'repair-road':s.road=true;s.timber--;text="The Keeper calls the lengths from the dry pier. You and Mara fit the boards; the last nail bends and Mara straightens it on a stone. A loaded cart rolls across. This time the axle does not have to leave the road.";break;
      case 'ready-ferry':s.ferry=true;if(n.hull<3)s.timber--;text=s.iven?"Iven works the ferry loose from the mooring wreckage. He runs his thumb along the patched bow. 'Two crates. The rest wait for the next trip.'":"You and Mara haul the ferry clear and test its patched bow with empty crates. Without Iven, a loaded round trip will take two shifts.";break;
      case 'recover-crew':
        text="Mara reads the names at the clinic gate. This time all four villagers answer. "+(s.iven?"Iven takes their wet coats from Mara's cart.":"Iven comes in behind them carrying a bent mooring hook. He puts it by the door, then goes to check the ferry line.")+" Senn takes the loft key from the table. 'There's seed above the grain. Leave that sack tied.'";
        s.people=4;s.iven=true;break;
      case 'retrieve-chest':s.medicine='ready';text="The chest is where Mara left it. You check the wax seal before lifting it. At the clinic steps the attendant clears a space; the packets are still dry.";break;
      case 'depot':s.medicine='ready';s.reserve_used=true;text="The depot keeper opens the reserve cupboard and counts out a fresh clinic load. She closes the empty box and writes its number on Mara's list. That reserve will need replacing.";break;
      case 'supply-clinic':s.medicine='supplied';s.timely=s.elapsed+1<=3;text=s.timely?"The attendant opens the chest before the morning queue reaches the stair. Mara sets up a table for clean dressings and leaves her coat on its peg.":"The morning queue has already dispersed when the chest arrives. The attendant asks the afternoon crew to call people back. Mara changes the time on her list; she does not erase it.";break;
      case 'grain':{
        const amount=Math.min(4-s.grain,s.road?4:s.ferry?2:1);s.grain+=amount;
        text=s.road?"The grain cart crosses the new boards with its wheels in the dry tracks. At the kitchen the receiving crew weighs each crate before emptying it into the bins.":s.ferry?(s.iven?`Iven watches the load settle against the bow. He takes the tiller. The kitchen receives ${amount} crate(s); the remaining grain stays in the loft.`:`You balance ${amount} crates against the bow and take the oars alone. The kitchen receives the load after the slow return trip.`):"You carry one crate along the ridge trail. Mara braces it when the path narrows. The kitchen gate opens; the next load will need another walk.";
        break;
      }
      case 'seed':s.seed='saved';text="The seed sack is on a shelf above the flour dust. Its tie is still tight. Senn's name is scratched on the shelf edge. You bring it to the clinic yard and set it on dry boards, away from Lio's kitchen load.";break;
      case 'plant':s.seed='sown';text="You cut a shallow drain along the upper planting strip. Senn tests the soil with her heel before opening the sack. She puts the first row in by hand. There is no harvest to count yet; only seed in ground that is no longer standing in water.";break;
      case 'close':text="Mara folds the work list around the loft key and hands it to the afternoon crew. The wagon driver calls from the road.";break;
    }
    s.elapsed+=choice.cost;s.time-=choice.cost;
    if(action==='close'||s.time===0) {
      s.ending=s.people===4&&s.iven&&s.medicine==='supplied'&&s.grain===4?'READY_FOR_NOON':'WORK_REMAINS';
      if(action!=='close')text+=' The noon wagon leaves; the remaining work passes to the afternoon crew.';
    }
    const result={action,cost:choice.cost,text,before,after:this.snapshot()};this.history.push(result);return result;
  }
  epilogue() {
    const s=this.state;if(!s.ending)throw new Error('Morning work is still open.');
    const lines=[s.people===4?"Mara closes the line for the mill party. Four names are accounted for in the clinic yard.":`${4-s.people} villagers still wait across the channel. Mara gives their locations to the afternoon crew before the wagon leaves.`,
      s.medicine==='supplied'?(s.timely?"The clinic has dry supplies in time for morning care.":"The clinic has dry supplies now. The afternoon crew is calling back the people who left its morning queue."):s.medicine==='ready'?"The dry chest waits on the clinic steps. The afternoon crew must help the attendant unpack it.":"The clinic shelf is still empty. Dry medicine is the first item on the afternoon list.",
      s.grain===4?"The kitchen crew fits the lids on four grain bins. Tonight's kitchen load is in place.":`The kitchen crew marks ${s.grain} of four grain crates received. ${4-s.grain} remain at the mill; another crew must bring them.`,
      s.seed==='sown'?"Senn stays by the planted strip to clear its drain. She will check the rows after the next rain.":s.seed==='saved'?"The seed sack is dry in the clinic yard. Mara marks a drained planting strip as the next job.":"The seed is still in the loft. Mara puts its shelf location beneath the grain entry.",
      s.road?("The causeway can carry the afternoon carts."+(s.ferry?" The ready ferry is tied above the landing as a second supply route.":"")):s.ferry?"The ferry is ready for the next loads. The causeway still needs boards.":"The ridge trail is the only usable supply route. The afternoon crew must open a faster crossing."];
    if(!s.iven)lines.push("Iven is still on the far side. Mara leaves his name beside the ferry inspection.");
    if(s.reserve_used)lines.push("The depot's reserve box is empty. Its number stays on the afternoon supply list.");
    if(!s.record_corrected)lines.push("The false council order is still on the public list. The Keeper leaves the measuring cord in the workshop.");
    return lines.join('\n\n');
  }
}
