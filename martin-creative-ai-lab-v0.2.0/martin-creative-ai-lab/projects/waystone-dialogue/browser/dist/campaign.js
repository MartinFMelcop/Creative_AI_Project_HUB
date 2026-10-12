import {Adventure,serialize as nightSave,restore as restoreNight} from './engine.js';
import {Morning} from './morning.js';
export class Campaign extends Adventure {
  constructor(){super();this.morning=null;}
  choices(){return this.morning?this.morning.choices():super.choices();}
  act(action) {
    if(action==='morning') {
      if(this.morning||!this.state.ending)throw new Error('The morning follows a completed night crossing.');
      const before=this.snapshot();this.morning=new Morning(before);
      const result={action,cost:0,text:this.morning.opening(),before,after:this.morning.snapshot()};
      this.history.push(result);return result;
    }
    if(!this.morning)return super.act(action);
    const result=this.morning.act(action);this.history.push(result);return result;
  }
}
export function serialize(game) {
  const data=nightSave(game);
  return game.morning?{...data,schema:2,engine_version:'0.4.0'}:data;
}
export function restore(data) {
  if(data?.schema===1) {
    const old=restoreNight(data),game=new Campaign();
    game.state=old.state;game.workshop=old.workshop;game.history=old.history;return game;
  }
  if(!data||data.format!=='waystone-save'||data.schema!==2||data.engine_version!=='0.4.0'
    ||!Array.isArray(data.actions)||data.actions.length>1024||data.actions.some(a=>typeof a!=='string'||a.length>32))throw new Error('Incompatible campaign save.');
  const game=new Campaign();for(const action of data.actions)game.act(action);return game;
}
