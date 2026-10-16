'use strict';
const $ = id => document.getElementById(id);
let workspace = 'kids', capabilities = null, reference = '', busy = false, lastJobs = '';
async function api(path, payload) {
  const response = await fetch(path, payload === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || 'Studio request failed.');
  return value;
}
function show(id, visible) { $(id).classList.toggle('hidden', !visible); }
function switchWorkspace(next) {
  workspace = next;
  const kids = next === 'kids';
  for (const name of ['kids', 'creator']) { $(name+'-tab').classList.toggle('active', name===next); $(name+'-tab').setAttribute('aria-pressed', String(name===next)); }
  $('breadcrumb').textContent = 'Workspace / '+(kids?'Kids Factory':'Creator Studio');
  $('eyebrow').textContent = kids?'SMALL CHARACTER. BIG ADVENTURES.':'BIG IDEAS. BEAUTIFUL FRAMES.';
  $('title').textContent = kids?'Make a little wonder.':'Make the scene yours.';
  $('subtitle').textContent = kids?'A familiar face. A fresh discovery. A story worth sharing.':'Cinematic moments, product stories and your next creative experiment.';
  $('chapter').textContent = kids?'01 / KIDS':'02 / CREATOR';
  show('kids-feature', kids); show('creator-feature', !kids);
  $('engine').querySelector('[value="blender"]').disabled = !kids;
  $('engine').value = kids?'':'wangp';
  $('prompt').placeholder = kids?'A tiny capybara discovers a glowing strawberry in a pastel garden. Gentle camera push, playful expression, warm morning light.':'A glass perfume bottle on warm stone, golden light moving through linen curtains. Slow cinematic orbit, soft shadows, premium product film.';
  $('form-message').textContent = '';
  updateEngine(); lastJobs=''; refreshJobs();
}
function updateModels() {
  const model = capabilities.models[$('model').value];
  const previous = $('mode').value;
  $('mode').replaceChildren(...model.modes.map(mode => new Option(mode==='text'?'Text prompt':'Reference image',mode)));
  if (model.modes.includes(previous)) $('mode').value=previous;
  $('resolution').replaceChildren(...model.resolutions.map(size=>new Option(size.replace('x',' × '),size)));
  $('steps').value=model.steps;
  show('reference-field', $('mode').value==='image');
}
function updateEngine() {
  const engine = $('engine').value;
  show('blender-fields', engine==='blender'); show('wangp-fields',engine==='wangp');
  $('engine-status').classList.remove('warning');
  let message='Choose Blender for the proven Pip episode, or WanGP for a new AI scene.';
  if (capabilities && engine==='blender') message=capabilities.blender?'Blender CPU worker is configured. Progress stays indeterminate during rendering.':'Blender is not configured yet. The original verified episode is preserved below.';
  if (capabilities && engine==='wangp') {
    const available=$('provider').value==='local'?capabilities.wangp_local:capabilities.wangp_cloud;
    message=available?(capabilities.gpu_generation_verified?'A WanGP MP4 has been generated and verified in this studio. Other models, settings and GPU locations still need testing.':'WanGP connection is configured; GPU generation is not yet verified. Longer clips and larger models need more resources.'):'GPU connection needed. No free GPU endpoint is configured for this location. Submitting records an actionable error; it does not spend money.';
    $('engine-status').classList.add('warning');
  }
  $('engine-status').textContent=message;
}
async function refreshJobs() {
  try {
    const jobs=(await api('/api/jobs')).filter(j=>j.spec.workspace===workspace);
    const serialized=JSON.stringify(jobs); if(serialized===lastJobs) return; lastJobs=serialized;
    $('job-count').textContent=jobs.length;
    $('jobs').replaceChildren();
    if(!jobs.length) {
      const box=document.createElement('div'); box.className='empty';
      const title=document.createElement('strong');title.textContent='A little room for your next big idea.';
      const line=document.createElement('p');line.textContent='Choose an engine and add a scene. Its progress and finished video will appear here.';
      box.append(title,line);$('jobs').append(box);return;
    }
    for(const job of jobs) {
      const row=document.createElement('article');row.className='job';
      const body=document.createElement('div'), title=document.createElement('strong'), detail=document.createElement('p');
      title.textContent=job.spec.engine==='blender'?'Pip & the giant strawberry':job.spec.prompt.slice(0,100);
      detail.textContent=`${job.spec.engine==='blender'?'Blender': 'WanGP · '+job.spec.model} / ${job.spec.duration}s / ${job.spec.resolution} · ${new Date(job.created*1000).toLocaleString()}`;
      body.append(title,detail);
      if(job.error){const error=document.createElement('p');error.className='error';error.textContent=job.error;body.append(error);}
      if(job.verification.decode_passed){const proof=document.createElement('p');proof.textContent=`Verified MP4 · ${job.verification.width} × ${job.verification.height} · ${job.verification.duration.toFixed(2)}s`;body.append(proof);}
      const state=document.createElement('div'),label=document.createElement('span'); label.className='job-state';label.textContent=job.state+' · '+job.phase;state.append(label);
      if(['queued','running','cancelling'].includes(job.state)){const bar=document.createElement('progress');bar.max=100;if(job.progress>0)bar.value=job.progress;bar.setAttribute('aria-label','Generation progress');state.append(bar);}
      const actions=document.createElement('div');actions.className='job-actions';
      if(job.download){const view=document.createElement('button');view.className='button secondary';view.textContent='View & download ↗';view.onclick=()=>preview(job.download,title.textContent);actions.append(view);}
      if(['queued','running'].includes(job.state)){const cancel=document.createElement('button');cancel.className='button secondary';cancel.textContent='Cancel';cancel.onclick=async()=>{try{await api(`/api/jobs/${job.id}/cancel`,{});await refreshJobs();}catch(e){$('form-message').textContent=e.message;}};actions.append(cancel);}
      row.append(body,state,actions);$('jobs').append(row);
    }
  }catch(e){$('form-message').textContent='Connection lost. Your history stays saved; reconnect to this studio.';}
}
function preview(url,title){$('preview-title').textContent=title;$('video').src=url;$('download').href=url+'?download=1';$('download').setAttribute('download','studio-video.mp4');$('preview').showModal();}
$('kids-tab').onclick=()=>switchWorkspace('kids');$('creator-tab').onclick=()=>switchWorkspace('creator');
$('engine').onchange=updateEngine;$('provider').onchange=updateEngine;$('model').onchange=updateModels;
$('mode').onchange=()=>show('reference-field',$('mode').value==='image');
$('close-preview').onclick=()=>$('preview').close();$('preview').addEventListener('close',()=>{$('video').pause();$('video').removeAttribute('src');$('video').load();});
$('watch').onclick=()=>{if(capabilities.sample)preview('/api/sample','Pip & the giant strawberry · verified Blender episode');else $('form-message').textContent='Set PIP_SAMPLE to your preserved MP4, or unpack the complete project ZIP to view the original episode.';};
$('reference').onchange=async()=>{
  reference='';const file=$('reference').files[0];if(!file)return;
  $('reference-status').textContent='Uploading…';
  try{
    if(file.size>8*1024*1024)throw new Error('Use an image under 8 MB.');
    const encoded=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.onerror=reject;r.readAsDataURL(file);});
    const result=await api('/api/references',{image:encoded});reference=result.id;
    $('reference-status').textContent=`Ready · ${result.width} × ${result.height} · Metadata removed`;
  }catch(e){$('reference-status').textContent=e.message;}
};
$('job-form').onsubmit=async event=>{
  event.preventDefault();if(busy)return;busy=true;$('submit').disabled=true;$('form-message').textContent='';
  try{
    const engine=$('engine').value;
    if(!engine)throw new Error('Choose your generation engine.');
    if(engine==='wangp'&&$('mode').value==='image'&&!reference)throw new Error('Upload a reference image first.');
    const spec={workspace,engine,episode:'strawberry',quality:$('quality').value,model:$('model').value,provider:$('provider').value,mode:$('mode').value,prompt:$('prompt').value,negative_prompt:$('negative').value,resolution:$('resolution').value,duration:Number($('duration').value),seed:Number($('seed').value),steps:Number($('steps').value),reference};
    await api('/api/jobs',spec);$('form-message').textContent='Added to your queue.';await refreshJobs();
  }catch(e){$('form-message').textContent=e.message;}finally{busy=false;$('submit').disabled=false;}
};
(async()=>{
  try{capabilities=await api('/api/capabilities');$('model').replaceChildren(...Object.entries(capabilities.models).map(([id,m])=>new Option(m.name,id)));updateModels();updateEngine();await refreshJobs();setInterval(refreshJobs,2000);}catch(e){$('form-message').textContent='Studio is unavailable. Start the Python server and reload.';}
})();
