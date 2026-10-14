(() => {
  'use strict';
  const byId=id=>document.getElementById(id);
  const record=JSON.parse(byId('record-data').textContent),actions=record.actions || [];
  const status={todo:'To do',doing:'In progress',blocked:'Blocked',done:'Done'};
  const fold=value=>value.normalize('NFKD').replace(/\p{M}/gu,'').toLowerCase();
  const date=value=>`${new Date(value).toLocaleString()} (${value})`;
  const node=(tag,text,className)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;};
  const button=(text,click)=>{const el=node('button',text);el.type='button';el.onclick=click;return el;};
  const owner=action=>action.owner_name===null?'Unassigned':action.owner_name;
  const pageSize=20;
  const byEntry=new Map(record.entries.map((entry,index)=>[entry.id,{entry,index}]));
  const records=record.entries.map(entry=>({kind:entry.kind,id:entry.id,time:entry.created_at,entry,text:fold(entry.body)}));
  for(const action of actions)for(const event of action.history)records.push({kind:'action',id:event.id,time:event.created_at,event,action,text:fold(`${event.action.title} ${event.action.note}`)});
  // Reading order merges the two streams; revision authority still comes from
  // the recorded revision numbers, not the machine's wall clock.
  records.sort((a,b)=>b.time.localeCompare(a.time)||a.kind.localeCompare(b.kind)||b.id-a.id);
  let workPage=0,resultPage=0,matches=records,openedFrom=null;
  document.title=`${record.project.name} · Reading copy`;
  byId('project-name').textContent=record.project.name;
  byId('snapshot-time').textContent=`Snapshot exported ${date(record.exported_at)}. This file does not receive later changes.`;
  byId('summary').textContent=`${record.entries.length} discussion/decision entries · ${actions.length} actions · ${records.length-record.entries.length} action revisions`;
  if(!Object.hasOwn(record,'actions'))byId('work-help').textContent='This earlier JSON export contains no action data. It does not establish whether actions existed in the workspace.';
  for(const name of [...new Set(actions.filter(a=>a.owner_name!==null).map(a=>a.owner_name))].sort((a,b)=>a.localeCompare(b))) {
    const option=node('option',name);option.value=JSON.stringify(name);byId('work-owner').append(option);
  }
  function range(count,page) {return count?`${page*pageSize+1}–${Math.min((page+1)*pageSize,count)} of ${count}`:'No matches';}
  function badge(value) {return node('span',status[value],`badge ${value}`);}
  function entryCard(entry) {
    const card=node('li');card.dataset.entry=entry.id;
    card.append(node('p',`${entry.kind==='decision'?'Decision':'Discussion note'} · ${entry.author} · ${date(entry.created_at)}`,'meta'),node('p',entry.body,'body'));
    return card;
  }
  function actionCard(action,heading='h3') {
    const card=node('div',undefined,'card');card.dataset.action=action.id;
    card.append(node(heading,action.title,'body'),badge(action.status),node('p',`Owner label: ${owner(action)} · revision ${action.revision}`,'meta'));
    card.append(node('p',action.note||'No update note recorded.','body'),node('p',`Updated ${date(action.updated_at)}`,'meta'));
    return card;
  }
  function drawWork() {
    const filtered=actions.filter(action=>(byId('work-status').value==='all'||action.status===byId('work-status').value)&&
      (byId('work-owner').value==='all'||JSON.stringify(action.owner_name)===byId('work-owner').value));
    workPage=Math.min(workPage,Math.max(0,Math.ceil(filtered.length/pageSize)-1));
    byId('work-count').textContent=filtered.length?`${range(filtered.length,workPage)} actions at export`:'No actions match these filters.';
    byId('work-list').replaceChildren(...filtered.slice(workPage*pageSize,(workPage+1)*pageSize).map(action=>{
      const item=node('li');item.dataset.action=action.id;
      item.append(node('h3',action.title,'body'),badge(action.status),node('p',`${owner(action)} · revision ${action.revision}`,'meta'),node('p',action.note||'No update note recorded.','body'));
      const open=button('Open decision and revisions',()=>showAction(action,action.history.at(-1),open));item.append(open);return item;
    }));
    byId('work-prev').disabled=workPage===0;byId('work-next').disabled=(workPage+1)*pageSize>=filtered.length;
  }
  function drawResults() {
    byId('result-count').textContent=`${range(matches.length,resultPage)} saved records`;
    byId('results').replaceChildren(...matches.slice(resultPage*pageSize,(resultPage+1)*pageSize).map(match=>{
      let item;
      if(match.entry)item=entryCard(match.entry);
      else {
        const snapshot=match.event.action;item=node('li');item.dataset.event=match.id;
        item.append(node('p',`Action revision ${snapshot.revision} · ${match.event.author} · ${date(match.time)}${snapshot.revision===match.action.revision?' · Current at export':' · Historical'}`,'meta'),node('h3',snapshot.title,'body'),badge(snapshot.status),node('p',snapshot.note||'No update note recorded.','body'));
      }
      const open=button('Open saved context',()=>match.entry?showEntry(match.entry,open):showAction(match.action,match.event,open));item.append(open);return item;
    }));
    byId('result-prev').disabled=resultPage===0;byId('result-next').disabled=(resultPage+1)*pageSize>=matches.length;
  }
  function search() {
    const query=byId('query').value,terms=fold(query.trim()).split(/\s+/u).filter(Boolean);
    if(query.length>160||terms.length>8||(!terms.length&&query.trim())) {
      matches=[];resultPage=0;drawResults();byId('result-count').textContent='Use up to 8 literal words and 160 characters, including at least one searchable character.';return;
    }
    const kind=byId('record-kind').value;
    matches=records.filter(match=>(kind==='all'||match.kind===kind)&&terms.every(term=>match.text.includes(term)));
    resultPage=0;drawResults();
  }
  function detail(title,opener) {
    openedFrom=opener;byId('detail-heading').textContent=title;
    byId('detail-body').replaceChildren();byId('detail').hidden=false;byId('detail-heading').focus();
  }
  function nearby(entry) {
    const {index}=byEntry.get(entry.id),list=node('ol');
    for(const neighbor of record.entries.slice(Math.max(0,index-2),index+3)) {
      const card=entryCard(neighbor);card.dataset.selected=String(neighbor.id===entry.id);list.append(card);
    }
    return list;
  }
  function linkedWork(entry,opener) {
    const section=node('section'),linked=actions.filter(action=>action.source_id===entry.id);
    section.append(node('h3','Linked work at export'));
    if(!linked.length){section.append(node('p','No linked actions in this export.'));return section;}
    const count=node('p',undefined,'meta'),list=node('ol'),nav=node('nav');nav.setAttribute('aria-label','Linked work pages');let page=0;
    const prev=button('Previous linked actions',()=>{page--;draw();}),next=button('Next linked actions',()=>{page++;draw();});
    function draw() {
      count.textContent=range(linked.length,page);
      list.replaceChildren(...linked.slice(page*pageSize,(page+1)*pageSize).map(action=>{
        const item=node('li');item.append(actionCard(action,'h4'),button('Open action history',()=>showAction(action,action.history.at(-1),opener)));return item;
      }));prev.disabled=page===0;next.disabled=(page+1)*pageSize>=linked.length;
    }
    nav.append(prev,next);section.append(count,list,nav);draw();return section;
  }
  function showEntry(entry,opener) {
    detail(entry.kind==='decision'?'Decision and nearby discussion':'Discussion context',opener);
    byId('detail-body').append(node('p','Up to two saved entries before and after the selected entry. They retain their own recorded order.','muted'),nearby(entry));
    if(entry.kind==='decision')byId('detail-body').append(linkedWork(entry,opener));
    byId('detail-heading').scrollIntoView({block:'start'});
  }
  function showAction(action,event,opener) {
    detail(`Action revision ${event.revision} and current work at export`,opener);
    const comparison=node('div',undefined,'comparison'),historical=actionCard(event.action,'h4'),current=actionCard(action,'h4');
    historical.prepend(node('h3',event.revision===action.revision?'Selected revision · current at export':'Selected revision · historical'));
    historical.append(node('p',`Recorded by ${event.author}`,'meta'));
    current.prepend(node('h3','Current at export'));
    comparison.append(historical,current);byId('detail-body').append(comparison);
    if(action.source_id!==null) {
      const source=byEntry.get(action.source_id).entry;
      byId('detail-body').append(node('h3','Source decision and nearby discussion'),nearby(source));
    } else byId('detail-body').append(node('p','This action has no linked decision source.','muted'));
    const history=node('section'),count=node('p',undefined,'meta'),list=node('ol'),nav=node('nav');nav.setAttribute('aria-label','Revision pages');
    history.append(node('h3','Complete revision history'),count,list,nav);byId('detail-body').append(history);
    // Start on the selected revision, including those beyond the live 50-event panel.
    let page=Math.floor((event.revision-1)/pageSize);
    const prev=button('Earlier revisions',()=>{page--;draw();}),next=button('Later revisions',()=>{page++;draw();});nav.append(prev,next);
    function draw() {
      count.textContent=`${range(action.history.length,page)} revisions`;
      list.replaceChildren(...action.history.slice(page*pageSize,(page+1)*pageSize).map(revision=>{
        const item=node('li');item.dataset.revision=revision.revision;item.dataset.selected=String(revision.id===event.id);
        item.append(node('p',`Revision ${revision.revision} · ${revision.author} · ${date(revision.created_at)}`,'meta'),node('h4',revision.action.title,'body'),badge(revision.action.status),node('p',`${owner(revision.action)} · ${revision.action.note||'No update note recorded.'}`,'body'));
        item.append(button('Compare this revision',()=>showAction(action,revision,opener)));return item;
      }));prev.disabled=page===0;next.disabled=(page+1)*pageSize>=action.history.length;
    }
    draw();byId('detail-heading').scrollIntoView({block:'start'});
  }
  byId('back').onclick=()=>{byId('detail').hidden=true;if(openedFrom?.isConnected)openedFrom.focus();else{byId('record-heading').tabIndex=-1;byId('record-heading').focus();}};
  for(const id of ['work-status','work-owner'])byId(id).onchange=()=>{workPage=0;drawWork();};
  byId('work-prev').onclick=()=>{workPage--;drawWork();};byId('work-next').onclick=()=>{workPage++;drawWork();};
  byId('search-form').onsubmit=event=>{event.preventDefault();search();};
  byId('result-prev').onclick=()=>{resultPage--;drawResults();};byId('result-next').onclick=()=>{resultPage++;drawResults();};
  byId('download-json').onclick=()=>{
    const url=URL.createObjectURL(new Blob([JSON.stringify(record)],{type:'application/json'}));
    const anchor=node('a');anchor.href=url;anchor.download=`project-${record.project.id}.json`;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  drawWork();drawResults();
})();
