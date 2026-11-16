// Lässt jede Suchanfrage durch die echte App laufen (gleiche match()-Funktion wie im Browser).
const { chromium } = require('/opt/node-tools/node_modules/playwright-core');
const fs = require('fs');
(async () => {
  const Q = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 420, height: 900 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://localhost:8765/'); await p.waitForSelector('.card');
  const out = [];
  for (const t of Q) {
    const { r, hs } = await p.evaluate(q => ({ r: match(q, "", "").slice(0, 5).map(x => ({
      t: x.p._t, url: x.p.url, pct: x.pct, zu: !!x.p._closed, hilfe: !!x.p.antragshilfe, kurz: x.p.kurz_eigen || "" })), hs: hinweise(q).map(h => h.t) }), t.q);
    const slugs = r.map(x => x.url.toLowerCase());
    const pos = t.e.length ? slugs.findIndex(u => t.e.some(e => u.includes(e.toLowerCase()))) : -1;
    let status;
    if (t.e.length) status = pos === 0 ? 'Treffer Platz 1' : pos > 0 && pos < 3 ? `Treffer Platz ${pos + 1}` : pos >= 3 ? `erst Platz ${pos + 1}` : 'nicht gefunden';
    else status = hs.length ? 'Lücke, Hinweis angezeigt' : r.length ? 'Lücke, aber Treffer angezeigt' : 'Lücke, keine Treffer';
    // Strenger als vorher: Lücken brauchen einen Hinweis (oder gar keine Treffer) und keinen Treffer mit hoher Passung,
    // verbotene Programme dürfen nicht unter den ersten 3 sein, ein geschlossenes Programm nie auf Platz 1.
    const bad = (t.n || []).some(n => slugs.slice(0, 3).some(u => u.includes(n)));
    const closedTop = t.e.length && r[0] && r[0].zu; // nur ein Fehler, wenn es ein offenes passendes Programm gibt
    // Lücke: Hinweis genügt; ohne Hinweis darf kein Treffer hohe Passung (≥ 60) haben
    let ok = t.e.length ? (pos >= 0 && pos < 3) : (hs.length > 0 || !r.some(x => x.pct >= 60));
    if (t.h && !hs.length) { ok = false; status += ', Hinweis fehlt'; }
    if (bad) { ok = false; status += ', unpassender Treffer'; }
    if (closedTop) { ok = false; status += ', geschlossenes Programm auf Platz 1'; }
    out.push({ ...t, status, ok, hinweise: hs, top: r });
  }
  fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 2));
  const n = out.filter(x => x.ok).length;
  console.log(`${n}/${out.length} bestanden; Fehler im Browser: ${errs.length}`);
  for (const x of out) if (!x.ok) console.log(`✗ [${x.k}] ${x.q} → ${x.status} :: ${x.top.slice(0, 3).map(y => y.t.slice(0, 45) + ' (' + y.pct + ')').join(' | ')}`);
  await b.close();
})();
