"""Build only public licensed Appunti model assets. No app or user data.
Creator Codex per Alessio. PROJECT; retire explicitly with distribution tooling.
"""
from pathlib import Path
import hashlib,json,subprocess,urllib.request,shutil
root=Path(__file__).resolve().parent;target=json.loads((root/'target-profile.json').read_text());source=json.loads((root/'upstream-profile.json').read_text());sources={x['path']:x for x in source['files']};out=Path('model-assets');out.mkdir();cache=Path('model-cache');cache.mkdir()
repo='alessiomattoccia1-sys/appunti-downloads';tag='models-20261105-qwen4b-small'
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
for item in target['files']:
 upstream=sources[item['path']];assert all(upstream[k]==item[k] for k in ['bytes','sha256'])
 if 'content' in item:assert item['content']==upstream['content'];continue
 url=upstream['url'];assert url.startswith(('https://huggingface.co/Systran/faster-whisper-base/','https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/','https://registry.ollama.ai/v2/library/qwen3/blobs/'))
 p=cache/item['sha256']
 with urllib.request.urlopen(url,timeout=90) as response,p.open('xb') as f:shutil.copyfileobj(response,f,4*1024*1024)
 assert p.stat().st_size==item['bytes'] and digest(p)==item['sha256']
 if 'parts' in item:
  with p.open('rb') as source_file:
   for part in item['parts']:
    dest=out/part['url'].rsplit('/',1)[-1];remaining=part['bytes']
    with dest.open('xb') as f:
     while remaining:
      block=source_file.read(min(4*1024*1024,remaining));assert block;f.write(block);remaining-=len(block)
    assert digest(dest)==part['sha256']
 else:shutil.copyfile(p,out/item['url'].rsplit('/',1)[-1])
shutil.copyfile(root/'target-profile.json',out/'model-profile.json');shutil.copyfile(root/'MODEL-NOTICES.txt',out/'MODEL-NOTICES.txt')
assets=list(out.iterdir());assert all(p.stat().st_size<2*1024**3 for p in assets)
subprocess.run(['gh','release','create',tag,'--repo',repo,'--draft','--title','Appunti — automatic local models','--notes','Original Qwen3 4B Q4_K_M, Whisper base and OCR. Automatically prepared by Appunti. All model and part SHA-256 hashes are pinned in model-profile.json; licenses in MODEL-NOTICES.txt. No user content.'],check=True)
subprocess.run(['gh','release','upload',tag,*map(str,assets),'--repo',repo],check=True)
releases=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases?per_page=100']))
release=next(x for x in releases if x['tag_name']==tag);remote={x['name']:x for x in release['assets']}
for p in assets:assert remote[p.name]['size']==p.stat().st_size and remote[p.name]['digest']=='sha256:'+digest(p)
subprocess.run(['gh','release','edit',tag,'--repo',repo,'--draft=false','--latest=false'],check=True)
print(json.dumps({'tag':tag,'verified_assets':len(assets),'original_qwen_preserved':True,'user_data':False}))
