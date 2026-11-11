// update-data.js — versi Vercel (tanpa secret key di frontend)
// POST dilakukan dari server / script dengan X-API-Key dari env, bukan dari browser.
// File ini hanya helper parse CSV lokal untuk mode demo.
function parseCSV(text){
  const lines=text.split(/\r?\n/).filter(l=>l.trim()!=="");
  if(lines.length<2) return [];
  const splitPipe=(line)=>{ const out=[]; let cur="", inQ=false; for(let i=0;i<line.length;i++){ const ch=line[i]; if(ch==='"'){ if(inQ&&line[i+1]==='"'){cur+='"'; i++;} else inQ=!inQ; } else if(ch==="|"&&!inQ){ out.push(cur); cur=""; } else cur+=ch; } out.push(cur); return out.map(s=>s.trim().replace(/^"|"$/g,"")); };
  const header=splitPipe(lines[0]); const idx=n=>header.findIndex(h=>h.toLowerCase().includes(n));
  return lines.slice(1).map(line=>{ const c=splitPipe(line); return {priority:parseInt(c[idx("priority")])||4, tanggal:c[idx("tanggal")]||"", platform:c[idx("platform")]||"", kategori:c[idx("kategori")]||"", topik:c[idx("topik")]||"", sentimen:c[idx("sentimen")]||"", url:c[idx("url")]||""}; });
}
async function updateDataEWS(file, crawlingDate){
  const f=file || document.getElementById("csvFile")?.files?.[0];
  const cd=crawlingDate || document.getElementById("crawlingInput")?.value?.trim() || "11-Nov-2026 13:21:52";
  if(!f) return [];
  // Di Vercel, POST dengan key harus dari backend/script, bukan browser. Di sini fallback parse lokal.
  const text=await f.text(); return parseCSV(text);
}
window.updateDataEWS=updateDataEWS;
