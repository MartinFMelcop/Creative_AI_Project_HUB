const { randomUUID }=require('node:crypto');

// Deliberately fictional collaboration records, never audience or delivery evidence.
function populate(store) {
  const person=store.session('Fixture Rook'),owner=store.session('Fixture Neri'),room=store.createRoom('Fictional cistern handover');
  store.work.join(room.id,person);store.work.join(room.id,owner);
  const append=(body,kind='note',roomId=room.id)=>store.append(person,{roomId,body,kind,clientId:randomUUID()}).message;
  append('Discuss a replacement before returning the pump.');
  const decision=append('Inspect the western valve before returning the loan.','decision');
  append('Keep the old part for inspection.');
  let action=store.work.apply(person,{op:'create',roomId:room.id,clientId:randomUUID(),sourceId:decision.id,title:'Return the borrowed pump',ownerId:owner.id}).action;
  const update=changes=>{action=store.work.apply(person,{op:'update',roomId:room.id,clientId:randomUUID(),actionId:action.id,expectedRevision:action.revision,title:action.title,ownerId:action.owner_id,status:action.status,note:action.note,...changes}).action;};
  update({status:'blocked',note:'Válvula presa no depósito. Waiting for a replacement.'});
  for(let index=0;index<60;index++)update({status:'doing',note:`Fictional pressure observation ${index}`});
  update({status:'done',note:'Replacement fitted; borrowed pump returned (fixture claim).',title:'Return completed pump'});
  for(let index=0;index<360;index++)append(`Fictional recent observation ${index}`,index<125?'decision':'note');
  const hostile='</script><img src="https://example.invalid/leak" onerror="globalThis.leaked=true"><b>Câble_%</b> "quote" & line\nsecond line';
  for(let index=0;index<25;index++)append(`${hostile} ${index}`);
  const unassigned=store.work.apply(person,{op:'create',roomId:room.id,clientId:randomUUID(),title:'Unassigned fixture check'}).action;
  const other=store.createRoom('Other fixture room');append('Other-room record must stay out','note',other.id);
  return {person,owner,room,decision,action,unassigned,other,append,update};
}
module.exports={populate};
