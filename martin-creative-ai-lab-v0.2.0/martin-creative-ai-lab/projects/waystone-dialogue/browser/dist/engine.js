import { Scene } from './scene.js';
import { DIALOGUE } from './dialogue.js';

// This bounded port preserves adventure.py 0.2.0; oracle tests compare transitions.
export const ENGINE_VERSION = '0.2.0';
export const CURRENTS = ['slack','pull','surge'];
export class Adventure {
  constructor() {
    this.state = {phase:'pack',kit:[],time:9,elapsed:0,route:null,light:false,
      roof:'waiting',iven:'waiting',waiting:2,saved:0,medicine:'waiting',bridge:null,
      hull:4,line:false,bank:'mill',aboard:0,ending:null};
    this.workshop = new Scene(); this.history = [];
  }
  snapshot() { return {version:ENGINE_VERSION,expedition:structuredClone(this.state),workshop:this.workshop.snapshot()}; }
  current(offset=0) { return CURRENTS[(this.state.elapsed+offset)%3]; }
  rescue_cost(who) {
    const s=this.state;
    return s.kit.includes('rope') || (who === 'roof' && (s.light || s.kit.includes('oil'))) ? 1 : 2;
  }
  choices() {
    const s=this.state, options=[], add=(name,label,cost=0)=>options.push({name,label,cost});
    if (s.ending) return [];
    if (s.phase === 'pack') {
      for (const name of ['rope','timber','oil']) if (s.kit.includes(name) || s.kit.length<2)
        add(name,`${s.kit.includes(name)?'Unpack':'Pack'} ${name}.`);
      if (s.kit.length===2) add('ready','Take this equipment to the workshop.');
      return options;
    }
    if (s.phase === 'workshop') return this.workshop.available_actions().map(name=>
      ({name,label:DIALOGUE.actions[name]+' [1 flood-window beat]',cost:1}));
    if (s.phase === 'route') {
      if (s.light) add('causeway','Follow the Waystone light to the mill yard. [1 beat]',1);
      add('ferry','Follow the lower track to the ferry. [2 beats]',2);
      add('retreat',"Return to high ground; abandon tonight's crossing.");
      return options.filter(c=>c.cost<=s.time);
    }
    if (s.phase==='causeway' || s.bank==='mill') {
      for (const [who,deadline,label] of [['roof',6,'Bring Lio and Senn down from the roof'],['iven',5,'Free Iven from the pinned jetty']]) {
        const cost=this.rescue_cost(who);
        if (s[who]==='waiting' && s.elapsed+cost<=deadline) {
          const method=who==='roof' && s.light ? 'Waystone signal' : who==='roof' && s.kit.includes('oil')
            ? 'burn oil as a signal; consume oil' : s.kit.includes('rope') ? 'consume rope' : 'work by hand';
          add(who,`${label}. [${cost} beat(s); ${method}; deadline ${deadline}]`,cost);
          if (who==='iven' && s.kit.includes('rope') && s.elapsed+2<=deadline)
            add('iven_hands','Free Iven by hand; keep the rope for the crossing. [2 beats; deadline 5]',2);
        }
      }
    }
    if (s.phase==='causeway') {
      if (!s.bridge) {
        if (s.kit.includes('timber')) add('span','Replace the missing boards. [2 beats; consume timber; permanent crossing]',2);
        if (s.kit.includes('rope')) add('lash','Rig a temporary footline. [1 beat; consume rope; slow evacuation]',1);
        add('wade','Mark a shallow footpath. [1 beat; slow evacuation; medicine cannot follow]',1);
      } else {
        const cost=s.bridge==='stable' || s.iven==='rescued' ? 1 : 2;
        if (s.waiting) {
          add('lead',`Lead all ${s.waiting} waiting villagers across. [${cost} beat(s); people only]`,cost);
          if (s.bridge==='stable' && s.medicine==='waiting') add('convoy','Move the people and medicine cart together. [2 beats]',2);
        }
        if (s.bridge!=='waded' && s.medicine==='waiting') add('medicine','Carry the medicine chest across separately. [1 beat]',1);
      }
    } else {
      const capacity=s.iven==='rescued' ? 3 : 2, occupied=s.aboard+Number(s.medicine==='aboard');
      if (s.bank==='mill') {
        if (s.waiting && occupied<capacity) add('board',`Board ${Math.min(s.waiting,capacity-occupied)} villager(s). [no time; ${capacity} cargo slots total]`);
        if (s.medicine==='waiting' && occupied<capacity) add('load','Load medicine in one cargo slot. [no time; unprotected surge spoils it]');
        if (occupied) add('unload','Put this load back on the mill bank. [no time]');
      }
      if (s.kit.includes('rope') && !s.line) add('secure','Rig a guide line across the channel. [1 beat; consume rope; prevents current damage]',1);
      if (s.kit.includes('timber')) add('reinforce','Add timber buoyancy to the ferry. [1 beat; consume timber; hull +3; medicine still vulnerable]',1);
      const cost=s.iven==='rescued' ? 1 : 2;
      if (occupied || s.bank==='road') add('row',`Row to the ${s.bank==='mill'?'road':'mill'} bank. [${cost} beat(s); current ${Array.from({length:cost},(_,i)=>this.current(i)).join('/')}]`,cost);
      add('hold','Stay tied to the jetty; let the current change. [1 beat; no hull damage]',1);
    }
    add('finish','End the operation; take the delivered people/cargo to shelter.');
    return options.filter(c=>c.cost<=s.time);
  }
  spend(cost) {
    const s=this.state, notices=[];
    s.time-=cost; s.elapsed+=cost;
    if (s.roof==='waiting' && s.elapsed>=6) {
      s.roof='sheltered'; notices.push('Lio waves once from the roof. He and Senn climb toward the north loft.\nThey are above the flood, but the road party cannot reach them tonight.');
    }
    if (s.iven==='waiting' && s.elapsed>=5) {
      s.iven='sheltered'; notices.push('The jetty tears loose. Iven scrambles onto the north shoal.\nHis boat remains here; he can no longer help steer it tonight.');
    }
    return notices;
  }
  close(forced=null) {
    const s=this.state;
    s.ending=forced || (s.saved===4 && s.medicine==='delivered' && s.iven==='rescued' ? 'FULL_RESCUE'
      : s.saved===4 ? 'PEOPLE_SAFE' : s.saved ? 'PARTIAL_CROSSING' : 'SHELTERED');
    s.phase='ending';
  }
  act(action) {
    const choice=this.choices().find(c=>c.name===action);
    if (!choice) throw new Error('That choice is unavailable. Use a listed choice.');
    const s=this.state,before=this.snapshot(); let text='',workshop_trace=null;
    const take=item=>{s.kit=s.kit.filter(x=>x!==item);};
    if (s.phase==='pack') {
      if (action==='ready') {s.phase='workshop';text=DIALOGUE.intro;}
      else if (s.kit.includes(action)) {take(action);text=`You return the ${action} to Mara's cart.`;}
      else {s.kit.push(action);s.kit.sort();text=`You take the ${action}.`;}
    } else if (s.phase==='workshop') {
      workshop_trace=this.workshop.act(action);
      text=`${workshop_trace.speaker}: ${workshop_trace.text}`;
      s.elapsed=this.workshop.state.turn; s.time=Math.max(0,9-s.elapsed);
      text+=this.spend(0).map(n=>'\n'+n).join('');
      if (this.workshop.state.ending) {
        s.light=this.workshop.state.ending==='COOPERATED'; s.phase='route';
        text+=s.light ? "\nThe Keeper seats the rune in a hooded lantern. 'Fit it at the causeway.\nThe boards are your problem. Use the light to call down the mill workers.'"
          : "\nMara lifts the medicine chest. 'Then we're using the ferry. Come on.'";
        if (!s.time) {text+='\nThe landing is already under water. Mara turns the cart toward high ground.';this.close();}
      }
    } else {
      switch(action) {
        case 'retreat': case 'finish':
          text="You call an end to the operation. Mara checks the names on her cart list."; this.close();break;
        case 'causeway': case 'ferry':
          s.route=s.phase=action;
          text=action==='causeway' ? 'You fit the rune into the causeway socket. Light picks out the mill yard,\nbut a gap cuts the line of stones.'
            : "The lower track ends at Iven's pinned ferry. The mill yard is still dry.\nMara: 'We'll load here. The high road is across the channel.'"; break;
        case 'roof': {
          s.roof='rescued';s.waiting+=2;let method;
          if (s.light) method='You sweep the Waystone light across the stair below the roof.';
          else if (s.kit.includes('oil')) {take('oil');method="You burn the oil in Mara's lamp and light the hidden stair.";}
          else if (s.kit.includes('rope')) {take('rope');method='You fasten your rope to the roof rail and lower the workers.';}
          else method='You and Mara drag a ladder through the mud and brace it against the mill.';
          text=method+"\nSenn comes down first. Lio follows with an empty flour sack.\n'It was full this morning,' he says. Mara takes it without answering.";break;
        }
        case 'iven': case 'iven_hands':
          s.iven='rescued';
          if (action==='iven' && s.kit.includes('rope')) {take('rope');text='You anchor the rope to a mill post; Iven pulls himself off the jetty.';}
          else text='You and Mara lever the jetty aside with a broken spar. Iven crawls clear.';
          text+="\nIven: 'I know where the channel pulls. Give me the tiller, not another order.'";
          if (this.workshop.state.flags.includes('FLAG_PLAYER_LIED')) text+='\nMara looks at you. This time you pass him the tiller without invoking the council.';break;
        case 'span': take('timber');s.bridge='stable';text="You fix the new boards between two sound stone piers. Mara tests them\nwith the cart's empty axle. It rolls straight; the road can carry the chest.";break;
        case 'lash': take('rope');s.bridge='temporary';text='The rope holds between the piers. Each crossing will need steady hands.\nMara leaves the cart behind; the medicine must be carried separately.';break;
        case 'wade': s.bridge='waded';text='You probe the submerged stones with a pole. The others can follow your\nfootmarks, slowly. The medicine chest would sit below the waterline.';break;
        case 'lead': case 'convoy':
          s.saved+=s.waiting;s.waiting=0;text='Mara counts the villagers onto the high road, one hand on each shoulder.';
          if(action==='convoy') {s.medicine='delivered';text+="\nThe cart follows. The chest's wax seal is dry.";}break;
        case 'medicine': s.medicine='delivered';text='You carry the chest between you and Mara. At the high road she checks\nthe wax seal, then sets it beyond the reach of the water.';break;
        case 'board': {
          const count=Math.min(s.waiting,(s.iven==='rescued'?3:2)-s.aboard-Number(s.medicine==='aboard'));
          s.aboard+=count;s.waiting-=count;text=`${count} villager(s) step aboard. Mara shifts their weight away from the cracked bow.`;break;
        }
        case 'load': s.medicine='aboard';text="Mara wedges the medicine chest beneath the seat. 'Dry until a surge gets in.'";break;
        case 'unload':
          s.waiting+=s.aboard;s.aboard=0;if(s.medicine==='aboard')s.medicine='waiting';
          text='You unload onto the mill bank and choose a different cargo order.';break;
        case 'secure': take('rope');s.line=true;text='You rig a line between the mill and the road bank. The ferry can now\nfollow it through the pull without taking water.';break;
        case 'reinforce': take('timber');s.hull+=3;text='You lash timber beneath the cracked bow. It adds buoyancy, not a lid\nfor the medicine chest; a surge can still wet the cargo.';break;
        case 'hold':text='You hold the ferry against the jetty. The current moves past; the hull stays intact.';break;
        case 'row': {
          const currents=Array.from({length:choice.cost},(_,i)=>this.current(i));
          const damage=s.line?0:currents.reduce((sum,c)=>sum+({slack:0,pull:1,surge:2}[c]),0);
          s.hull=Math.max(0,s.hull-damage);text=`You cross through ${currents.join(' then ')}. The hull loses ${damage}.`;
          if (!s.line && currents.includes('surge') && s.medicine==='aboard') {
            s.medicine='spoiled';text+='\nWater enters the medicine chest. Mara prises it open; the paper packets run to pulp.';
          }
          if (!s.hull) {
            text+="\nThe bow gives way. Everyone aboard catches the jetty's safety chains.\nYou pull them onto the nearest bank; the crossing is over.";
            if(s.medicine==='aboard')s.medicine='spoiled';this.close('BOAT_LOST');
          } else {
            s.bank=s.bank==='mill'?'road':'mill';
            if(s.bank==='road') {
              s.saved+=s.aboard;s.aboard=0;if(s.medicine==='aboard')s.medicine='delivered';
              text+='\nThe passengers step onto the high road. Mara marks their names.';
            } else text+='\nThe empty ferry returns to the mill bank.';
          }break;
        }
      }
      text+=this.spend(choice.cost).map(n=>'\n'+n).join('');
      if(!s.ending && !s.time) {text+='\nThe landing disappears under the flood. There is no time for another trip.';this.close();}
    }
    const result={action,cost:choice.cost,text,before,after:this.snapshot(),workshop_trace};
    this.history.push(result);return result;
  }
  epilogue() {
    const s=this.state;if(!s.ending)throw new Error('The operation is still open.');
    const lines=[`Ending: ${s.ending}`,`High-road arrivals: ${s.saved}/4. Medicine: ${s.medicine}.`];
    lines.push(s.saved===4 ? 'At the shelter Mara calls four names. Four people answer. Senn sits beside\nthe stove, both hands around a mug. Lio sets his empty flour sack beneath her wet boots.'
      : s.saved ? 'Mara seats the arrivals by the stove and writes the missing names for\nthe morning crew. The others shelter at the mill or north loft tonight.'
      : 'Mara turns the cart toward the hill shelter. No one reached the high road\nthrough your crossing. The mill party must wait above the flood until morning.');
    lines.push(s.medicine==='delivered' ? 'The clinic chest arrives sealed. Mara hands it to the night attendant\nbefore she takes off her wet coat.'
      : s.medicine==='spoiled' ? 'The night attendant tips water from the chest and reaches for the last dry\nbandages. Mara takes back her cart list and adds a fresh clinic load for morning.'
      : 'The medicine is still at the mill. Mara puts it first on the morning list.');
    lines.push(s.iven==='rescued' ? 'Iven reaches shelter with the party. He asks who has dry boots for tomorrow.'
      : "Iven is beyond tonight's reach; the morning crew must check the jetty and north shoal.");
    if(s.bridge==='stable') lines.push("The Waystone marks a repaired causeway. Tomorrow's carts have a road again.");
    else if(s.bridge) lines.push("The Waystone still burns, but tomorrow's crew must replace your temporary crossing.");
    else if(s.route==='ferry' && s.hull && s.iven==='rescued') lines.push('Iven leaves the ferry tied above the landing. The village keeps its river route.');
    if(this.workshop.state.flags.includes('FLAG_PLAYER_LIED')) lines.push(this.workshop.state.apology_due
      ? 'Your false council order remains uncorrected. The Keeper will hear about the crossing,\nbut Mara will not carry that order back as fact.'
      : "In the morning the Keeper asks Mara about the council order. 'Withdrawn,'\nshe says. Then she hands over the crossing crew's repair list.");
    return lines.join('\n\n');
  }
}

export function serialize(game) {
  const data={format:'waystone-save',schema:1,engine_version:ENGINE_VERSION,actions:game.history.map(h=>h.action)};
  if(data.actions.length>1024)throw new Error('This journal exceeds the 1,024-decision save limit. The crossing is still playable, but this journey cannot be saved.');
  return data;
}
export function restore(data) {
  // Replay accepted decisions, never trust a supplied snapshot or HTML.
  if (!data || data.format!=='waystone-save' || data.schema!==1 || data.engine_version!==ENGINE_VERSION
      || !Array.isArray(data.actions) || data.actions.length>1024 || data.actions.some(a=>typeof a!=='string' || a.length>32))
    throw new Error('This file is not a compatible Waystone save.');
  const game=new Adventure();
  for (const action of data.actions) game.act(action);
  return game;
}
