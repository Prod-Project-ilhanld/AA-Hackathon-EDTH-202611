(function () {
"use strict";
const M = JSON.parse(document.getElementById("data").textContent);
const $ = (id) => document.getElementById(id);
const W = M.world, TM = M.time, link = M.link, plan = M.plan;
const hasPlan = !!plan;
const acById = {}; M.aircraft.forEach((a) => { acById[a.id] = a; });
const coById = {}; W.contacts.forEach((c) => { coById[c.id] = c; });
const N = hasPlan ? M.tracks[M.aircraft[0].id].p.length : 1;
const state = { t: 0, playing: false, speed: 8, sel: null, hover: null, labels: true, trails: "all", dark: false,
  focusGroup: null,
  show: { zones: true, protect: true, ranges: false, homes: true, routes: true, links: true, marks: true }, layers: {} };
(M.layers || []).forEach((l, i) => { state.layers[i] = l.visible !== false; });
let dirty = true;
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const ICON = 95; // taille visuelle fixe des appareils et contacts (le monde fait des milliers de metres)

// ---------- data access ----------
function fidx(t) { return Math.min(Math.max(t / TM.dt, 0), N - 1); }
function posAt(id, t) {
  const tr = M.tracks[id]; if (!tr) return null;
  const f = fidx(t), i = Math.floor(f), j = Math.min(i + 1, N - 1), a = tr.p[i], b = tr.p[j];
  if (!a && !b) return null; if (!a) return b; if (!b) return a;
  const u = f - i; return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u];
}
const statusAt = (id, t) => (M.tracks[id] ? M.tracks[id].s[Math.min(Math.floor(fidx(t)), N - 1)] : "g");
const energyAt = (id, t) => (M.tracks[id] ? M.tracks[id].e[Math.min(Math.floor(fidx(t)), N - 1)] : 0);
const STATUS = { g: "au sol", f: "en vol", o: "observation", x: "engage (consomme)", l: "atterri", h: "en attente", r: "retour", L: "perdu (batterie)", F: "en panne" };
const typeKey = (a) => (a.type === "scout" ? "scout" : a.sub === "heavy" ? "heavy" : "light");
const typeLabel = (a) => (a.type === "scout" ? "eclaireur" : "effecteur " + (a.sub === "heavy" ? "lourd" : "leger"));
const reclassAt = (cid, t) => !!(link && link.events.some((e) => e.kind === "reclassify" && e.contact === cid && e.t <= t));
const FLYING = { f: 1, o: 1, h: 1, r: 1 };
const ALT_SCALE = 5; // exageration visuelle de l'altitude pour qu'elle se voie dans la scene 3D

// ---------- scene 3D : socle, cameraorbite, pioche ----------
const scene3 = new THREE.Scene();
const camera3 = new THREE.PerspectiveCamera(50, 1, 1, 200000);
let renderer3 = null;
const raycaster = new THREE.Raycaster();
const ndc = new THREE.Vector2();
const orbit = { tx: 0, ty: 0, tz: 0, radius: 4000, theta: Math.PI * 0.22, phi: 1.0 };
function colorHex(varName) { return new THREE.Color(css(varName) || "#888"); }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function updateCamera() {
  const r = orbit.radius, th = orbit.theta, ph = orbit.phi;
  camera3.position.set(orbit.tx + r * Math.sin(ph) * Math.sin(th), orbit.ty + r * Math.cos(ph), orbit.tz + r * Math.sin(ph) * Math.cos(th));
  camera3.lookAt(orbit.tx, orbit.ty, orbit.tz);
}
function fitView() {
  const b = W.bounds;
  const bw = Math.max(b[1] - b[0], 200), bh = Math.max(b[3] - b[2], 200);
  orbit.tx = (b[0] + b[1]) / 2; orbit.ty = 0; orbit.tz = (b[2] + b[3]) / 2;
  orbit.radius = Math.max(bw, bh) * 0.6; orbit.theta = Math.PI * 0.22; orbit.phi = 1.0;
  updateCamera(); dirty = true;
}
function groundColors() {
  scene3.background = colorHex("--map");
  scene3.fog.color = colorHex("--map");
  grid.material.color = colorHex("--grid"); grid.material.opacity = 0.55;
  ambient.color = colorHex("--text"); sun.color = new THREE.Color(0xffffff);
}

// ---------- socle de la scene (terrain, grille, lumieres) ----------
const b0 = W.bounds, worldW = Math.max(b0[1] - b0[0], 400) * 1.6, worldH = Math.max(b0[3] - b0[2], 400) * 1.6;
const worldCx = (b0[0] + b0[1]) / 2, worldCz = (b0[2] + b0[3]) / 2;
scene3.fog = new THREE.Fog(0x05080a, 1, Math.max(worldW, worldH) * 2.4);
// terrain : relief doux (bosses pseudo-aleatoires, deterministe) + teinte terrain militaire, vert-brun non uniforme
function hashN(x, y) { const s = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453; return s - Math.floor(s); }
function bumps(x, y) {
  let h = 0;
  h += Math.sin(x * 0.00055 + 1.7) * Math.cos(y * 0.0006) * 1;
  h += Math.sin(x * 0.0013 - y * 0.0009 + 4.1) * 0.5;
  h += (hashN(Math.round(x / 180), Math.round(y / 180)) - 0.5) * 0.6;
  return h;
}
const relief = Math.max(worldW, worldH) * 0.012; // amplitude du relief, discrete pour ne pas genes la lecture tactique
const segs = 48;
const groundGeo = new THREE.PlaneGeometry(worldW, worldH, segs, segs);
const gcol = [];
const gpos = groundGeo.attributes.position;
for (let i = 0; i < gpos.count; i++) {
  const lx = gpos.getX(i), ly = gpos.getY(i); // plan local, avant rotation : x,y = etendue, z = hauteur
  const wx = lx + worldCx, wy = -ly + worldCz;
  const h = bumps(wx, wy) * relief;
  gpos.setZ(i, h);
  const shade = 0.5 + bumps(wx * 1.7, wy * 1.7) * 0.18 + h / relief * 0.08;
  const c = new THREE.Color(0x3a3f22).multiplyScalar(clamp(shade, 0.35, 0.95));
  gcol.push(c.r, c.g, c.b);
}
groundGeo.setAttribute("color", new THREE.Float32BufferAttribute(gcol, 3));
groundGeo.computeVertexNormals();
const groundMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, metalness: 0 });
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2; ground.position.set(worldCx, -0.5, worldCz); scene3.add(ground);
const grid = new THREE.GridHelper(Math.max(worldW, worldH), 24, 0x39ffa4, 0x39ffa4);
grid.position.set(worldCx, 0.3, worldCz); grid.material.transparent = true; scene3.add(grid);
const ambient = new THREE.AmbientLight(0xffffff, 0.55); scene3.add(ambient);
const sun = new THREE.DirectionalLight(0xbfe9ff, 0.9); sun.position.set(worldCx + worldW * 0.3, Math.max(worldW, worldH) * 0.5, worldCz - worldH * 0.2); scene3.add(sun);
const sun2 = new THREE.PointLight(0xff9d1a, 0.4, Math.max(worldW, worldH) * 1.5); sun2.position.set(worldCx, 600, worldCz); scene3.add(sun2);
// elements de decor (rochers/caisses) : purement visuels, ne genent pas la lecture tactique
(function scatterProps() {
  const rockGeo = new THREE.DodecahedronGeometry(1, 0);
  const crateGeo = new THREE.BoxGeometry(1, 1, 1);
  for (let i = 0; i < 26; i++) {
    const rx = worldCx + (hashN(i, 3.1) - 0.5) * worldW * 0.92, rz = worldCz + (hashN(i, 7.7) - 0.5) * worldH * 0.92;
    const isCrate = hashN(i, 9.4) > 0.78;
    const m = new THREE.Mesh(isCrate ? crateGeo : rockGeo, new THREE.MeshStandardMaterial({ color: isCrate ? 0x6b5a33 : 0x3f4436, roughness: 1 }));
    const sc = isCrate ? 12 + hashN(i, 1.2) * 8 : 8 + hashN(i, 2.4) * 18;
    m.scale.set(sc, sc * (isCrate ? 1 : 0.7), sc); m.position.set(rx, sc * 0.3, rz); m.rotation.y = hashN(i, 5.5) * 6.28;
    scene3.add(m);
  }
})();

// ---------- formes des drones (silhouette distincte par type) ----------
function buildDrone(type) {
  const g = new THREE.Group();
  const scale = type === "heavy" ? 1.45 : type === "scout" ? 0.62 : 1;
  const col = colorHex("--" + type);
  const bodyMat = new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: 0.35, roughness: 0.45, metalness: 0.35 });
  const armMat = new THREE.MeshStandardMaterial({ color: 0x1a1f1d, roughness: 0.6 });
  const rotorMat = new THREE.MeshStandardMaterial({ color: col, transparent: true, opacity: 0.45, side: THREE.DoubleSide });
  const body = new THREE.Mesh(new THREE.BoxGeometry(16 * scale, 6 * scale, 24 * scale), bodyMat);
  g.add(body);
  const armLen = 15 * scale;
  const armGeo = new THREE.CylinderGeometry(1.1 * scale, 1.1 * scale, armLen, 6);
  const rotorGeo = new THREE.CylinderGeometry(6 * scale, 6 * scale, 0.6, 10);
  [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([sxn, szn]) => {
    const arm = new THREE.Mesh(armGeo, armMat); arm.rotation.z = Math.PI / 2;
    arm.position.set(sxn * armLen * 0.55, 2 * scale, szn * armLen * 0.55); g.add(arm);
    const rotor = new THREE.Mesh(rotorGeo, rotorMat); rotor.position.set(sxn * armLen, 3.4 * scale, szn * armLen); g.add(rotor);
  });
  if (type === "scout") {
    const sensor = new THREE.Mesh(new THREE.SphereGeometry(3.4, 8, 8), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.4 }));
    sensor.position.set(0, -1, 13 * scale); g.add(sensor);
  }
  g.traverse((o) => { if (o.isMesh) { o.userData.bodyMat = o === body; } });
  g.scale.setScalar(ICON / 22);
  return { group: g, bodyMat, haloColor: col };
}
const droneCache = {};
function droneTemplate(type) { if (!droneCache[type]) droneCache[type] = buildDrone(type); return droneCache[type]; }

// ---------- appareils : une entree 3D persistante par appareil ----------
const acEntries = {};
if (hasPlan) M.aircraft.forEach((a) => {
  const tk = typeKey(a);
  const built = buildDrone(tk);
  const group = built.group;
  const halo = new THREE.Mesh(new THREE.TorusGeometry(ICON * 0.62, 2.6, 6, 20), new THREE.MeshBasicMaterial({ color: built.haloColor, transparent: true, opacity: 0.85 }));
  halo.rotation.x = Math.PI / 2; halo.visible = false; group.add(halo);
  const selRing = new THREE.Mesh(new THREE.TorusGeometry(ICON * 0.82, 2, 6, 24), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9 }));
  selRing.rotation.x = Math.PI / 2; selRing.visible = false; group.add(selRing);
  group.children.forEach((m) => { if (m.isMesh) m.userData.pick = { kind: "a", id: a.id }; });
  scene3.add(group);
  // route complete, trace statique discrete (la portion volee n'est pas isolee dynamiquement, simplification assumee)
  const tr = M.tracks[a.id];
  const pts = tr.p.filter(Boolean).map((p) => new THREE.Vector3(p[0], p[2] * ALT_SCALE, p[1]));
  const routeGeo = new THREE.BufferGeometry().setFromPoints(pts.length ? pts : [new THREE.Vector3(), new THREE.Vector3()]);
  const routeMat = new THREE.LineBasicMaterial({ color: colorHex("--" + tk), transparent: true, opacity: 0.35 });
  const route = new THREE.Line(routeGeo, routeMat); scene3.add(route);
  const label = labelSprite(a.id, css("--" + tk) || "#fff");
  label.scale.set(150, 38, 1); label.visible = false; scene3.add(label);
  acEntries[a.id] = { group, halo, selRing, route, label, bodyMat: built.bodyMat, type: tk };
});

// ---------- contacts : construits une fois, mis a jour (couleur/visibilite) ----------
const contactEntries = {};
function contactGeo(cls) {
  if (cls === "hostile") return new THREE.OctahedronGeometry(ICON * 0.42);
  if (cls === "friendly") return new THREE.BoxGeometry(ICON * 0.6, ICON * 0.3, ICON * 0.6);
  return new THREE.SphereGeometry(ICON * 0.36, 12, 10);
}
function labelSprite(text, color) {
  const c = document.createElement("canvas"); c.width = 256; c.height = 64; const g = c.getContext("2d");
  g.font = "600 30px 'Space Grotesk', system-ui, sans-serif"; g.fillStyle = color; g.textBaseline = "middle"; g.fillText(text, 2, 32);
  const tex = new THREE.CanvasTexture(c); tex.minFilter = THREE.LinearFilter;
  const spr = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  spr.scale.set(240, 60, 1); spr.renderOrder = 10;
  return spr;
}
W.contacts.forEach((c) => {
  const col = colorHex("--" + c.cls);
  const mat = new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: 0.3, transparent: c.cls === "unknown", opacity: c.cls === "unknown" ? 0.25 : 1, wireframe: c.cls === "unknown" });
  const mesh = new THREE.Mesh(contactGeo(c.cls), mat);
  mesh.position.set(c.x, ICON * 0.3, c.y);
  mesh.userData.pick = { kind: "c", id: c.id };
  scene3.add(mesh);
  const label = labelSprite(c.id + (c.points ? " " + c.points + "p" : ""), css("--text") || "#cfe");
  label.position.set(c.x, ICON * 0.3 + 46, c.y);
  scene3.add(label);
  const reclassRing = new THREE.Mesh(new THREE.TorusGeometry(ICON * 0.7, 2, 6, 20), new THREE.MeshBasicMaterial({ color: colorHex("--bad"), transparent: true, opacity: 0.8 }));
  reclassRing.rotation.x = Math.PI / 2; reclassRing.position.copy(mesh.position); reclassRing.visible = false; scene3.add(reclassRing);
  const servedRing = new THREE.Mesh(new THREE.TorusGeometry(ICON * 0.78, 2, 6, 20), new THREE.MeshBasicMaterial({ color: colorHex("--ok"), transparent: true, opacity: 0.85 }));
  servedRing.rotation.x = Math.PI / 2; servedRing.position.copy(mesh.position); servedRing.visible = false; scene3.add(servedRing);
  contactEntries[c.id] = { mesh, mat, label, reclassRing, servedRing, base: c };
});

// ---------- zones interdites (cylindres translucides, hauteur = plafond) ----------
const zoneEntries = [];
function makeZone(z, fresh) {
  const col = colorHex("--zone");
  const mat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.1, side: THREE.DoubleSide });
  const cyl = new THREE.Mesh(new THREE.CylinderGeometry(z.r, z.r, Math.max(z.top, 10), 28, 1, true), mat);
  cyl.position.set(z.x, Math.max(z.top, 10) / 2, z.y); scene3.add(cyl);
  const edge = new THREE.Mesh(new THREE.TorusGeometry(z.r, 3, 4, 32), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.8 }));
  edge.rotation.x = Math.PI / 2; edge.position.set(z.x, 0.5, z.y); scene3.add(edge);
  const pulse = new THREE.Mesh(new THREE.TorusGeometry(z.r, 3, 4, 32), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0 }));
  pulse.rotation.x = Math.PI / 2; pulse.position.set(z.x, 0.6, z.y); scene3.add(pulse);
  const label = labelSprite(z.id + " · jusqu'a " + Math.round(z.top) + " m", css("--zone") || "#ff9d1a");
  label.position.set(z.x, Math.max(z.top, 10) + 50, z.y); scene3.add(label);
  zoneEntries.push({ cyl, edge, pulse, label, z, fresh });
}
W.zones.forEach((z) => makeZone(z, false));
if (link) link.events.filter((e) => e.kind === "popup_zone").forEach((e, i) => makeZone({ id: "NEW" + (i + 1), x: e.center[0], y: e.center[1], r: e.radius_m, top: e.top_m, t0: e.t }, true));

// ---------- zones protegees et portees d'observation (anneaux au sol) ----------
const ringEntries = [];
function groundRing(x, y, r, color, opacity) {
  const ring = new THREE.Mesh(new THREE.RingGeometry(r - 3, r, 48), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2; ring.position.set(x, 0.8, y); scene3.add(ring);
  return ring;
}
W.contacts.forEach((c) => {
  if (c.cls === "friendly" || c.cls === "civilian") {
    ringEntries.push({ kind: "protect", ring: groundRing(c.x, c.y, W.rules.protect, colorHex("--" + c.cls), 0.4) });
    ringEntries.push({ kind: "ranges", ring: groundRing(c.x, c.y, W.rules.collateral, colorHex("--" + c.cls), 0.2) });
  }
  if (c.cls === "hostile" || c.cls === "unknown") ringEntries.push({ kind: "ranges", ring: groundRing(c.x, c.y, W.rules.R_obs, colorHex("--" + c.cls), 0.22) });
});

// ---------- bases ----------
const homeEntries = [];
if (hasPlan) M.aircraft.forEach((a) => {
  const h = new THREE.Mesh(new THREE.BoxGeometry(14, 14, 14), new THREE.MeshBasicMaterial({ color: colorHex("--muted"), wireframe: true }));
  h.position.set(a.home[0], 7, a.home[1]); scene3.add(h); homeEntries.push(h);
});

// ---------- calques utilisateur (Viewer.layer) ----------
const layerGroups = [];
(M.layers || []).forEach((l, i) => {
  const grp = new THREE.Group();
  const col = new THREE.Color(l.color || "#ff7b72");
  l.items.forEach((it) => {
    if (it.kind === "point") {
      const m = new THREE.Mesh(new THREE.SphereGeometry(it.r || 10, 10, 8), new THREE.MeshBasicMaterial({ color: it.color ? new THREE.Color(it.color) : col }));
      m.position.set(it.x, 20, it.y); grp.add(m);
      if (it.label) { const s = labelSprite(it.label, it.color || l.color || "#ff7b72"); s.position.set(it.x, 60, it.y); grp.add(s); }
    } else if (it.kind === "line") {
      const pts = it.pts.map((p) => new THREE.Vector3(p[0], 15, p[1]));
      grp.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: it.color ? new THREE.Color(it.color) : col, transparent: true, opacity: it.alpha || 0.85 })));
    } else if (it.kind === "circle") {
      grp.add(groundRing(it.x, it.y, it.r, it.color ? new THREE.Color(it.color) : col, 0.5));
    } else if (it.kind === "label") {
      const s = labelSprite(it.label, it.color || l.color || "#ff7b72"); s.position.set(it.x, 30, it.y); grp.add(s);
    }
  });
  grp.children.forEach((c) => scene3.add(c));
  layerGroups.push({ grp, t0: l.t0, t1: l.t1 });
});

// ---------- marques : observation et engagements (pool reutilise) ----------
const markEntries = M.marks.map((m) => {
  if (m.kind === "observe") {
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineDashedMaterial({ color: colorHex("--scout"), dashSize: 20, gapSize: 12, transparent: true, opacity: 0.8 }));
    line.visible = false; scene3.add(line); return { m, line };
  }
  const ring = new THREE.Mesh(new THREE.TorusGeometry(10, 3, 6, 24), new THREE.MeshBasicMaterial({ color: colorHex("--hostile"), transparent: true, opacity: 0 }));
  ring.rotation.x = Math.PI / 2; const c = coById[m.contact]; if (c) ring.position.set(c.x, ICON * 0.4, c.y); ring.visible = false; scene3.add(ring); return { m, ring };
});

// ---------- violations (anneaux au sol, rejoues autour de v.t) ----------
const violationEntries = hasPlan ? plan.violations.map((v) => {
  const ids = v.pair || (v.aircraft ? [v.aircraft] : []);
  const rings = ids.map(() => { const r = new THREE.Mesh(new THREE.TorusGeometry(ICON * 0.9, 3, 6, 24), new THREE.MeshBasicMaterial({ color: colorHex("--bad"), transparent: true, opacity: 0 })); r.rotation.x = Math.PI / 2; r.visible = false; scene3.add(r); return r; });
  const link3 = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineBasicMaterial({ color: colorHex("--bad"), transparent: true, opacity: 0 }));
  link3.visible = false; scene3.add(link3);
  return { v, rings, link3 };
}) : [];

// ---------- liens de messages (bassin reutilisable) ----------
const LINK_POOL = 36;
const linkPool = [];
if (link) for (let i = 0; i < LINK_POOL; i++) {
  const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineDashedMaterial({ color: colorHex("--muted"), dashSize: 30, gapSize: 16, transparent: true, opacity: 0.4 }));
  l.visible = false; scene3.add(l); linkPool.push(l);
}
const linkBySec = {}, linkDelivered = {};
if (link) link.links.forEach((l) => { const s = Math.floor(l[0]) + 1; (linkBySec[s] = linkBySec[s] || []).push(l); if (l[3]) linkDelivered[l[0] + ":" + l[1]] = true; });

// ---------- boucle de mise a jour de la scene ----------
function updateScene() {
  const t = state.t;
  zoneEntries.forEach((ze) => {
    const show = state.show.zones && t >= (ze.z.t0 || 0);
    ze.cyl.visible = ze.edge.visible = ze.label.visible = show;
    if (ze.fresh && show) {
      const age = t - (ze.z.t0 || 0);
      if (age < 6) { ze.pulse.visible = true; ze.pulse.scale.setScalar(1 + age * 0.35); ze.pulse.material.opacity = 0.6 * (1 - age / 6); }
      else ze.pulse.visible = false;
    }
  });
  ringEntries.forEach((re) => { re.ring.visible = !!state.show[re.kind]; });
  homeEntries.forEach((h) => { h.visible = state.show.homes; });
  layerGroups.forEach((lg) => { const on = state.layers[layerGroups.indexOf(lg)] !== false; const inWindow = (lg.t0 == null || t >= lg.t0) && (lg.t1 == null || t <= lg.t1); lg.grp.children.forEach((c) => (c.visible = on && inWindow)); });
  // contacts : reclassification, service, labels
  W.contacts.forEach((c) => {
    const e = contactEntries[c.id], re = reclassAt(c.id, t), cls = re ? "friendly" : c.cls;
    if (e._cls !== cls) { e._cls = cls; const col = colorHex("--" + cls); e.mat.color = col; e.mat.emissive = col; }
    e.reclassRing.visible = re;
    const sv = M.served[c.id]; e.servedRing.visible = sv !== undefined && sv <= t;
    e.label.visible = state.labels;
  });
  // appareils
  if (hasPlan) M.aircraft.forEach((a) => {
    const e = acEntries[a.id], st = statusAt(a.id, t), p = posAt(a.id, t);
    const dim = state.focusGroup && e.type !== state.focusGroup;
    if (!p || st === "x") { e.group.visible = false; e.route.visible = false; e.label.visible = false; return; }
    e.group.visible = true;
    e.group.position.set(p[0], p[2] * ALT_SCALE, p[1]);
    const q = posAt(a.id, t + 1.5), q0 = posAt(a.id, t - 1.5);
    if (q && q0 && (Math.abs(q[0] - q0[0]) + Math.abs(q[1] - q0[1])) > 0.5) e.group.rotation.y = Math.atan2(q[0] - q0[0], q[2] - q0[1] /* placeholder, corrected below */);
    if (q && q0) { const dx = q[0] - q0[0], dz = q[1] - q0[1]; if (Math.abs(dx) + Math.abs(dz) > 0.5) e.group.rotation.y = Math.atan2(dx, dz); }
    const op = (st === "g" || st === "l" ? 0.55 : 1) * (dim ? 0.15 : 1);
    e.bodyMat.opacity = op; e.bodyMat.transparent = op < 1; e.group.traverse((o) => { if (o.isMesh && o.material && o.userData.pick) { o.material.transparent = op < 1; o.material.opacity = op; } });
    e.halo.visible = !dim && (st === "o" || st === "h" || st === "r");
    if (e.halo.visible) e.halo.material.color = colorHex(st === "h" ? "--warn" : st === "r" ? "--civilian" : "--" + e.type);
    e.selRing.visible = !dim && (state.sel === a.id || state.hover === a.id);
    const showRoute = state.show.routes && !dim && (state.trails === "all" || (state.trails === "selected" && (state.sel === a.id || state.hover === a.id)));
    e.route.visible = showRoute; e.route.material.opacity = state.sel === a.id ? 0.85 : 0.3;
    e.label.visible = state.labels && !dim && !!FLYING[st];
    if (e.label.visible) e.label.position.set(p[0], p[2] * ALT_SCALE + ICON * 0.9, p[1]);
  });
  // marques
  markEntries.forEach(({ m, line, ring }) => {
    if (m.kind === "observe") {
      const on = state.show.marks && t >= m.t0 && t <= m.t1; line.visible = on;
      if (on) { const p = posAt(m.aid, t), c = coById[m.contact]; if (p && c) { const pts = [new THREE.Vector3(p[0], p[2] * ALT_SCALE, p[1]), new THREE.Vector3(c.x, ICON * 0.3, c.y)]; line.geometry.setFromPoints(pts); line.computeLineDistances(); } }
    } else {
      const on = state.show.marks && t >= m.t && t - m.t < 4; ring.visible = on;
      if (on) { const u = (t - m.t) / 4; ring.scale.setScalar(1 + u * 2.4); ring.material.opacity = 0.9 * (1 - u); }
    }
  });
  // violations
  violationEntries.forEach(({ v, rings, link3 }) => {
    const show = v.t !== null && v.t !== undefined && Math.abs(t - v.t) <= 4;
    const ids = v.pair || (v.aircraft ? [v.aircraft] : []);
    const ps = show ? ids.map((id) => posAt(id, v.t)).filter(Boolean) : [];
    rings.forEach((r, i) => { r.visible = show && !!ps[i]; if (ps[i]) { r.position.set(ps[i][0], ps[i][2] * ALT_SCALE + 4, ps[i][1]); const u = Math.abs(t - v.t) / 4; r.scale.setScalar(1 + u * 0.5); r.material.opacity = 0.9 * (1 - u); } });
    link3.visible = show && ps.length === 2;
    if (link3.visible) { link3.geometry.setFromPoints([new THREE.Vector3(ps[0][0], ps[0][2] * ALT_SCALE + 4, ps[0][1]), new THREE.Vector3(ps[1][0], ps[1][2] * ALT_SCALE + 4, ps[1][1])]); link3.material.opacity = 0.8; }
  });
  // liens de messages
  if (link) {
    const sec = Math.floor(t), items = (state.show.links && t >= link.t_loss) ? (linkBySec[sec] || []) : [];
    linkPool.forEach((lp, i) => {
      const l = items[i]; if (!l) { lp.visible = false; return; }
      const a = posAt(l[1], t), bpos = posAt(l[2], t); if (!a || !bpos) { lp.visible = false; return; }
      lp.visible = true; lp.geometry.setFromPoints([new THREE.Vector3(a[0], a[2] * ALT_SCALE + 4, a[1]), new THREE.Vector3(bpos[0], bpos[2] * ALT_SCALE + 4, bpos[1])]); lp.computeLineDistances();
      lp.material.color = colorHex(l[3] ? "--ok" : "--muted"); lp.material.opacity = l[3] ? 0.55 : 0.3;
    });
  }
}

// ---------- rendu ----------
function render3() {
  const wrap = $("mapwrap"); const rect = wrap.getBoundingClientRect();
  if (!renderer3) { renderer3 = new THREE.WebGLRenderer({ canvas: $("map"), antialias: true, alpha: false }); renderer3.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); groundColors(); }
  const w = Math.max(1, rect.width), h = Math.max(1, rect.height);
  if (renderer3.domElement.width !== Math.round(w * renderer3.getPixelRatio()) || renderer3.domElement.height !== Math.round(h * renderer3.getPixelRatio())) { renderer3.setSize(w, h, true); camera3.aspect = w / h; camera3.updateProjectionMatrix(); }
  updateCamera(); updateScene(); renderer3.render(scene3, camera3);
}

// ---------- timeline and altitude strip (inchange, 2D) ----------
function fitCanvas(cv) {
  const r = cv.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  const w = Math.max(1, Math.round(r.width * dpr)), h = Math.max(1, Math.round(r.height * dpr));
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  const ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w: r.width, h: r.height };
}
const T0 = TM.t0, T1 = Math.max(TM.t1, TM.t0 + 1);
const tx = (t, w, pad) => pad + ((t - T0) / (T1 - T0)) * (w - 2 * pad);
function drawTimeline() {
  const { ctx, w, h } = fitCanvas($("tl")); ctx.clearRect(0, 0, w, h);
  const pad = 8, y = h / 2;
  ctx.fillStyle = css("--panel2"); ctx.fillRect(pad, y - 3, w - 2 * pad, 6);
  ctx.fillStyle = css("--accent"); ctx.globalAlpha = 0.5; ctx.fillRect(pad, y - 3, tx(state.t, w, pad) - pad, 6); ctx.globalAlpha = 1;
  if (link) { const X = tx(link.t_loss, w, pad); ctx.strokeStyle = css("--bad"); ctx.setLineDash([3, 3]); ctx.beginPath(); ctx.moveTo(X, 2); ctx.lineTo(X, h - 2); ctx.stroke(); ctx.setLineDash([]); ctx.fillStyle = css("--bad"); ctx.font = "10px 'Space Grotesk', system-ui, sans-serif"; ctx.fillText("coupure", X + 3, 10);
    link.events.forEach((e) => { const x = tx(e.t, w, pad); ctx.beginPath(); ctx.moveTo(x, y - 8); ctx.lineTo(x + 5, y); ctx.lineTo(x, y + 8); ctx.lineTo(x - 5, y); ctx.closePath(); ctx.fillStyle = css("--warn"); ctx.fill(); }); }
  M.marks.forEach((m) => { const x = tx(m.kind === "engage" ? m.t : m.t1, w, pad); ctx.beginPath();
    if (m.kind === "engage") { ctx.strokeStyle = css("--hostile"); ctx.lineWidth = 2; ctx.moveTo(x - 3, y - 11); ctx.lineTo(x + 3, y - 5); ctx.moveTo(x + 3, y - 11); ctx.lineTo(x - 3, y - 5); ctx.stroke(); }
    else { ctx.arc(x, y - 8, 2.8, 0, 6.2832); ctx.fillStyle = css("--scout"); ctx.fill(); } });
  if (hasPlan) plan.violations.forEach((v) => { if (v.t === null || v.t === undefined) return; const x = tx(v.t, w, pad); ctx.fillStyle = css("--bad"); ctx.beginPath(); ctx.moveTo(x, y + 4); ctx.lineTo(x - 4, y + 12); ctx.lineTo(x + 4, y + 12); ctx.closePath(); ctx.fill(); });
  const X = tx(state.t, w, pad); ctx.fillStyle = css("--text"); ctx.fillRect(X - 1, 3, 2, h - 6);
}
function drawAlt() {
  const { ctx, w, h } = fitCanvas($("alt")); ctx.clearRect(0, 0, w, h);
  const padL = 34, padR = 8, padT = 6, padB = 16, zmax = Math.max(W.rules.z_max * 1.15, 40);
  const X = (t) => padL + ((t - T0) / (T1 - T0)) * (w - padL - padR), Y = (z) => h - padB - (z / zmax) * (h - padT - padB);
  ctx.fillStyle = css("--warn"); ctx.globalAlpha = 0.07; ctx.fillRect(padL, Y(W.rules.z_min), w - padL - padR, Y(0) - Y(W.rules.z_min)); ctx.fillRect(padL, padT, w - padL - padR, Y(W.rules.z_max) - padT); ctx.globalAlpha = 1;
  ctx.strokeStyle = css("--grid"); ctx.fillStyle = css("--muted"); ctx.font = "10px 'Space Grotesk', system-ui, sans-serif"; ctx.lineWidth = 1;
  [0, W.rules.z_min, W.rules.z_max].forEach((z) => { ctx.beginPath(); ctx.moveTo(padL, Y(z)); ctx.lineTo(w - padR, Y(z)); ctx.stroke(); ctx.fillText(Math.round(z) + " m", 2, Y(z) + 3); });
  if (!hasPlan) { ctx.fillText("aucun plan charge", padL + 8, h / 2); return; }
  const to = Math.floor(fidx(T1));
  M.aircraft.forEach((a) => {
    const tr = M.tracks[a.id], isSel = state.sel === a.id; ctx.beginPath(); let go = false;
    for (let i = 0; i <= to; i++) { const p = tr.p[i]; if (!p) { go = false; continue; } const x = X(i * TM.dt), y = Y(p[2]); if (!go) { ctx.moveTo(x, y); go = true; } else ctx.lineTo(x, y); }
    ctx.strokeStyle = css("--" + typeKey(a)); ctx.lineWidth = isSel ? 2.4 : 1; ctx.globalAlpha = state.sel ? (isSel ? 1 : 0.18) : 0.55; ctx.stroke(); ctx.globalAlpha = 1;
  });
  ctx.fillStyle = css("--muted"); ctx.fillText("altitude dans le temps" + (state.sel ? " · " + state.sel + " en surbrillance" : ""), padL + 4, padT + 9);
  ctx.fillStyle = css("--text"); ctx.fillRect(X(state.t) - 1, padT, 2, h - padT - padB);
}

// ---------- command strip: live KPIs ----------
function renderHud() {
  const t = state.t;
  const total = M.aircraft.length;
  let flying = 0;
  M.aircraft.forEach((a) => { if (FLYING[statusAt(a.id, t)]) flying++; });
  const servable = W.contacts.filter((c) => c.points);
  const servedNow = servable.filter((c) => M.served[c.id] !== undefined && M.served[c.id] <= t).length;
  const coverage = servable.length ? Math.round((100 * servedNow) / servable.length) : 0;
  const activeAlerts = alertList.filter((al) => al.t <= t && t - al.t < 20).length;
  const degraded = !!(link && t >= link.t_loss);
  const invalid = hasPlan && plan.valid === false;
  const groups = [
    { key: "scout", label: "Eclaireurs", value: M.aircraft.filter((a) => typeKey(a) === "scout").length },
    { key: "light", label: "Eff. legers", value: M.aircraft.filter((a) => typeKey(a) === "light").length },
    { key: "heavy", label: "Eff. lourds", value: M.aircraft.filter((a) => typeKey(a) === "heavy").length },
  ];
  let html = `<div class="kpi"><div class="k-label">En vol</div><div class="k-value">${flying}<span class="k-sub"> / ${total}</span></div></div>`;
  html += `<div class="kpi"><div class="k-label">Couverture</div><div class="k-value">${coverage}%</div><div class="k-sub">${servedNow} / ${servable.length} traites</div></div>`;
  html += `<div class="kpi${activeAlerts ? " degraded" : ""}"><div class="k-label">Alertes actives</div><div class="k-value">${activeAlerts}</div></div>`;
  html += `<div class="kpi${degraded || invalid ? " degraded" : ""}"><div class="k-label">Etat</div><div class="k-value" style="font-size:13px">${invalid ? "PLAN INVALIDE" : degraded ? "MODE DEGRADE" : "NOMINAL"}</div></div>`;
  groups.forEach((g) => { html += `<div class="kpi${state.focusGroup === g.key ? " active" : ""}" data-g="${g.key}"><div class="k-label">${g.label}</div><div class="k-value">${g.value}</div></div>`; });
  $("hud").innerHTML = html;
  $("hud").querySelectorAll("[data-g]").forEach((el) => { el.onclick = () => { state.focusGroup = state.focusGroup === el.dataset.g ? null : el.dataset.g; dirty = true; renderHud(); }; });
}

// ---------- priority alert feed ----------
function libelleEvent(e) {
  if (e.kind === "popup_zone") return "Nouvelle zone interdite (rayon " + Math.round(e.radius_m) + " m)";
  if (e.kind === "reclassify") return "Contact " + e.contact + " reclasse ami";
  return e.kind + (e.contact ? " · " + e.contact : "") + (e.aircraft ? " · " + e.aircraft : "");
}
function buildAlerts() {
  const items = [];
  if (hasPlan) plan.violations.forEach((v) => { items.push({ t: v.t === null || v.t === undefined ? 0 : v.t, sev: "bad", text: (v.rule || "regle") + " : " + esc(v.msg.replace(/^R\d+ \([^)]*\)\s*/, "")) }); });
  if (link) link.events.forEach((e) => { items.push({ t: e.t, sev: e.kind === "popup_zone" ? "bad" : "warn", text: esc(libelleEvent(e)) }); });
  items.sort((a, b) => a.t - b.t);
  return items;
}
let alertList = [];
function renderAlerts() {
  const t = state.t;
  const visible = alertList.filter((al) => al.t <= t + 0.01).slice(-6).reverse();
  $("alerts").innerHTML = visible.map((al) => `<div class="alert sev-${al.sev}" data-t="${al.t}"><span class="a-sev"></span><span class="a-t">${Math.round(al.t)}s</span><span>${al.text}</span></div>`).join("");
  $("alerts").querySelectorAll(".alert").forEach((el) => { el.onclick = () => setT(Math.max(0, +el.dataset.t - 2)); });
}

// ---------- guided demo scenario ----------
function buildDemoSteps() {
  const steps = [{ t: T0, text: `Scenario : ${M.meta.level} graine ${M.meta.seed}, ${M.aircraft.length} appareils, ${W.contacts.length} contacts.` }];
  const firstEngage = M.marks.find((m) => m.kind === "engage");
  if (firstEngage) { const c = coById[firstEngage.contact]; steps.push({ t: firstEngage.t, text: `Premier contact traite : ${firstEngage.contact}${c && c.points ? " (" + c.points + " points)" : ""}.` }); }
  if (link) {
    steps.push({ t: link.t_loss, text: "Perte de liaison : la politique embarquee prend le relais." });
    const rec = link.events.find((e) => e.kind === "reclassify");
    if (rec) steps.push({ t: rec.t, text: `Contact ${rec.contact} reclasse ami a t = ${Math.round(rec.t)} s.` });
  }
  if (hasPlan && plan.violations.length) {
    const v = plan.violations.find((v) => v.t !== null && v.t !== undefined);
    if (v) steps.push({ t: v.t, text: `Alerte : ${v.rule || "regle"} a t = ${Math.round(v.t)} s.` });
  }
  const bilan = hasPlan ? (plan.valid === false ? "Bilan : plan invalide, 0 point." :
    `Bilan : score ${plan.score !== null && plan.score !== undefined ? plan.score : plan.points}, ${Object.keys(M.served).length} contacts traites sur ${W.contacts.filter((c) => c.points).length}.`) : "Fin du scenario.";
  steps.push({ t: T1, text: bilan });
  steps.sort((a, b) => a.t - b.t);
  return steps;
}
let demoRunning = false;
function runDemo() {
  if (demoRunning) return;
  demoRunning = true; state.playing = false; $("play").textContent = "▶"; fitView();
  const steps = buildDemoSteps();
  let i = 0;
  const step = () => {
    if (i >= steps.length) { $("narration").classList.remove("on"); demoRunning = false; return; }
    const s = steps[i++]; setT(s.t);
    const n = $("narration"); n.textContent = s.text; n.classList.add("on");
    setTimeout(step, 3200);
  };
  step();
}

// ---------- side panel ----------
const TABS = [["aircraft", "Appareils"], ["contacts", "Contacts"], ["issues", "Alertes"]];
if (link) TABS.push(["link", "Liaison"]);
TABS.push(["layers", "Calques"]);
let curTab = hasPlan ? (plan.violations.length ? "issues" : "aircraft") : "contacts";
function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
function buildCard() {
  const c = $("card"); let h = "";
  if (!hasPlan) {
    const n = (k) => W.contacts.filter((x) => x.cls === k).length;
    h = `<div class="big">${M.aircraft.length} appareils</div><div class="sub">${n("hostile")} hostiles · ${n("unknown")} inconnus · ${n("friendly")} amis · ${n("civilian")} civils · ${W.zones.length} zones. Aucun plan charge.</div>`;
  } else if (link) {
    const r = link.retention, ok = !link.failed.length;
    h = `<span class="pill ${ok ? "ok" : "bad"}">${ok ? "execution terminee sans echec" : "ECHEC : retention 0"}</span>
      <div class="big" style="margin-top:6px">${r === null ? "–" : Math.round(r * 100) + "%"} <span class="sub" style="font-size:13px;font-weight:400">retention</span></div>
      <div class="bar"><i style="width:${r === null ? 0 : r * 100}%;background:var(--${ok ? "ok" : "bad"})"></i></div>
      <div class="parts"><span>points <b>${link.points}</b> sur <b>${link.oracle_points === null ? "–" : link.oracle_points}</b> (oracle)</span><span><b>${link.messages}</b> messages · <b>${link.per_min}</b> par appareil-min</span><span>${link.setting[0]} m · ${link.setting[1]} B/s</span></div>
      ${link.failed.slice(0, 3).map((f) => `<div class="sub" style="color:var(--bad);margin-top:4px">${esc(f)}</div>`).join("")}`;
  } else if (plan.valid) {
    const p = plan.score_parts;
    h = `<span class="pill ok">valide</span><div class="big" style="margin-top:6px">${plan.score}</div><div class="sub">score</div>
      <div class="parts"><span>points <b>${p.points}</b></span><span>energie <b>−${p.energy_cost}</b> (${plan.energy} Wh)</span><span>effecteurs <b>−${p.effector_cost}</b> (${plan.effectors})</span></div>`;
  } else {
    h = `<span class="pill bad">INVALIDE</span><div class="big" style="margin-top:6px">0</div><div class="sub">${plan.violations.length} violation${plan.violations.length === 1 ? "" : "s"} : un plan invalide vaut 0 point. Voir Alertes.</div>`;
  }
  c.innerHTML = h;
}
function buildTabs() {
  $("tabs").innerHTML = TABS.map(([k, n]) => `<button role="tab" data-t="${k}" class="${k === curTab ? "on" : ""}">${n}${k === "issues" && hasPlan ? " (" + plan.violations.length + ")" : ""}</button>`).join("");
  $("tabs").onclick = (e) => { const b = e.target.closest("button"); if (!b) return; curTab = b.dataset.t; buildTabs(); showPanel(); };
}
function showPanel() { document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("on", p.id === "p-" + curTab)); }
function buildPanels() {
  const P = $("panels"); P.innerHTML = "";
  const mk = (id, html) => { const d = document.createElement("div"); d.className = "panel"; d.id = "p-" + id; d.innerHTML = html; P.appendChild(d); return d; };
  mk("aircraft", `<table><thead><tr><th>Appareil</th><th>Statut</th><th>Alt</th><th>Energie</th></tr></thead><tbody>${M.aircraft.map((a) => `<tr class="row" data-a="${a.id}"><td><span class="dot" style="background:var(--${typeKey(a)})"></span>${a.id}</td><td data-s></td><td data-z></td><td><span class="ebar"><i data-e></i></span></td></tr>`).join("")}</tbody></table>`).onclick = (e) => { const r = e.target.closest("tr[data-a]"); if (r) select(r.dataset.a === state.sel ? null : r.dataset.a); };
  mk("contacts", `<table><thead><tr><th>Contact</th><th>Points</th><th>Besoins</th><th>Fenetre</th><th>Traite</th></tr></thead><tbody>${W.contacts.map((c) => `<tr class="row" data-c="${c.id}"><td><span class="dot" style="background:var(--${c.cls})"></span>${c.id} <span class="sub">${c.cls}</span></td><td>${c.points || ""}</td><td>${Object.entries(c.needs || {}).filter((x) => x[1] > 0).map((x) => x[1] + " " + x[0][0].toUpperCase()).join(" ")}</td><td>${c.window ? Math.round(c.window[0]) + "–" + Math.round(c.window[1]) + " s" : ""}</td><td data-sv></td></tr>`).join("")}</tbody></table>`).onclick = (e) => { const r = e.target.closest("tr[data-c]"); if (r) { const sv = M.served[r.dataset.c]; if (sv !== undefined) setT(sv); } };
  const issues = hasPlan ? plan.violations : [];
  mk("issues", issues.length ? issues.map((v, i) => `<div class="issue" data-i="${i}"><b>${esc(v.rule)}</b> ${esc(v.msg.replace(/^R\d+ \([^)]*\)\s*/, ""))}${v.t !== null && v.t !== undefined ? ` <span class="sub">· t = ${Math.round(v.t)} s</span>` : ""}</div>`).join("") : `<div class="empty">${hasPlan ? (link ? "Aucune regle enfreinte sur cette execution." : "Aucune violation : le plan est valide.") : "Charger un plan pour voir son verdict."}</div>`).onclick = (e) => {
    const r = e.target.closest(".issue"); if (!r) return; const v = issues[+r.dataset.i]; if (v.t !== null && v.t !== undefined) setT(Math.max(0, v.t - 2)); const id = (v.pair && v.pair[0]) || v.aircraft; if (id) select(id); };
  if (link) mk("link", `<div class="sub" style="padding:6px">Coupure a t = ${link.t_loss} s. Evenements (cliquer pour chercher) :</div>${link.events.map((e) => `<div class="issue" data-t="${e.t}"><b style="color:var(--warn)">${e.kind}</b> t = ${e.t}${e.contact ? " · " + e.contact : ""}${e.aircraft ? " · " + e.aircraft : ""}${e.radius_m ? " · r " + e.radius_m + " m" : ""}</div>`).join("")}
    <div class="sub" style="padding:8px 6px 2px">Messages envoyes jusqu'ici (12 derniers), gris = non livres :</div><div class="log" id="msglog"></div>`).onclick = (e) => { const r = e.target.closest(".issue"); if (r) setT(Math.max(0, +r.dataset.t - 3)); };
  const flags = [["zones", "Zones interdites"], ["protect", "Zones protegees"], ["ranges", "Portees d'observation et de collateral"], ["homes", "Bases"], ["routes", "Trainees et routes"], ["marks", "Faisceaux d'observation et flashs d'engagement"]];
  if (link) flags.push(["links", "Liens de messages"]);
  const L = mk("layers", `<div class="layers"><h4>Carte</h4>${flags.map(([k, n]) => `<label><input type="checkbox" data-f="${k}" ${state.show[k] ? "checked" : ""}> ${n}</label>`).join("")}
    <h4>Trainees</h4><label><input type="radio" name="tr" value="all" checked> tous les appareils</label><label><input type="radio" name="tr" value="selected"> selection ou survol uniquement</label><label><input type="radio" name="tr" value="none"> aucune</label>
    ${(M.layers || []).length ? "<h4>Vos calques</h4>" + M.layers.map((l, i) => `<label><input type="checkbox" data-l="${i}" ${state.layers[i] ? "checked" : ""}><span class="swatch" style="background:${esc(l.color)}"></span> ${esc(l.name)} <span class="sub">(${l.items.length})</span></label>`).join("") : "<h4>Vos calques</h4><div class=\"sub\" style=\"padding:2px 6px\">Aucun pour l'instant. <code>Viewer(...).layer(\"nom\", points=[...], lines=[...])</code> dessine les votres.</div>"}</div>`);
  L.onchange = (e) => { const t = e.target; if (t.dataset.f) state.show[t.dataset.f] = t.checked; if (t.dataset.l) state.layers[t.dataset.l] = t.checked; if (t.name === "tr") state.trails = t.value; dirty = true; };
  showPanel();
}
function updatePanels() {
  const t = state.t;
  document.querySelectorAll("#p-aircraft tr[data-a]").forEach((r) => {
    const id = r.dataset.a, st = statusAt(id, t), p = posAt(id, t), e = energyAt(id, t), wh = acById[id].wh;
    r.querySelector("[data-s]").textContent = hasPlan ? STATUS[st] || st : "";
    r.querySelector("[data-z]").textContent = p && st !== "x" ? Math.round(p[2]) + " m" : "";
    const bar = r.querySelector("[data-e]"); bar.style.width = (wh ? (100 * e) / wh : 0) + "%"; bar.style.background = e / wh < 0.2 ? "var(--bad)" : "var(--ok)";
    r.classList.toggle("sel", state.sel === id);
    r.classList.toggle("dim", !!(state.focusGroup && typeKey(acById[id]) !== state.focusGroup));
  });
  document.querySelectorAll("#p-contacts tr[data-c]").forEach((r) => {
    const sv = M.served[r.dataset.c]; const td = r.querySelector("[data-sv]");
    td.textContent = sv === undefined ? (hasPlan ? "–" : "") : (sv <= t ? "✓ " : "· ") + Math.round(sv) + " s"; td.style.color = sv !== undefined && sv <= t ? "var(--ok)" : "var(--muted)";
  });
  if (link) { const el = $("msglog"); if (el) el.innerHTML = link.sent.filter((s) => s[0] <= t).slice(-12).map((s) => `<div class="${linkDelivered[s[0] + ":" + s[1]] ? "" : "lost"}">${s[0]} ${s[1]} ${esc(s[2])}</div>`).join(""); }
  renderHud(); renderAlerts();
}

// ---------- controls ----------
function select(id) { state.sel = id; dirty = true; updatePanels(); }
function setT(v) { state.t = Math.min(Math.max(v, T0), T1); dirty = true; updateClock(); updatePanels(); }
function updateClock() { $("clock").textContent = `t = ${state.t.toFixed(1)} s / ${Math.round(T1)} s`; if (link) { const cut = state.t >= link.t_loss; const b = $("banner"); b.textContent = cut ? "LIAISON COUPEE · la politique embarquee prend le relais" : "liaison active · suit le plan"; b.className = cut ? "cut" : ""; } else $("banner").style.display = "none"; }
function togglePlay() { if (!hasPlan) return; if (state.t >= T1 - 0.01) state.t = T0; state.playing = !state.playing; $("play").textContent = state.playing ? "❚❚" : "▶"; last = performance.now(); }
let last = performance.now();
function frame(now) {
  const dtm = Math.min((now - last) / 1000, 0.1); last = now;
  if (state.playing) { state.t += dtm * state.speed; if (state.t >= T1) { state.t = T1; state.playing = false; $("play").textContent = "▶"; } dirty = true; updateClock(); }
  render3();
  if (dirty) { dirty = false; drawTimeline(); drawAlt(); if (!state.playing || Math.floor(now / 100) !== frame.lastPanel) { frame.lastPanel = Math.floor(now / 100); updatePanels(); } }
  requestAnimationFrame(frame);
}
function seekFromEvent(cv, e, pad) { const r = cv.getBoundingClientRect(); const u = (e.clientX - r.left - pad) / (r.width - 2 * pad); setT(T0 + Math.min(Math.max(u, 0), 1) * (T1 - T0)); }
function bindScrub(cv, pad) { let down = false; cv.addEventListener("pointerdown", (e) => { down = true; cv.setPointerCapture(e.pointerId); seekFromEvent(cv, e, pad); }); cv.addEventListener("pointermove", (e) => { if (down) seekFromEvent(cv, e, pad); }); cv.addEventListener("pointerup", () => { down = false; }); }
function pickAt(clientX, clientY, rect) {
  ndc.x = ((clientX - rect.left) / rect.width) * 2 - 1; ndc.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(ndc, camera3);
  const targets = []; Object.values(acEntries).forEach((e) => e.group.visible && e.group.children.forEach((c) => c.isMesh && targets.push(c)));
  Object.values(contactEntries).forEach((e) => targets.push(e.mesh));
  const hits = raycaster.intersectObjects(targets, false);
  for (const h of hits) { if (h.object.userData.pick) return h.object.userData.pick; }
  return null;
}
function hoverInfo(pick) {
  if (!pick) return null;
  if (pick.kind === "a") { const a = acById[pick.id], st = statusAt(pick.id, state.t), p = posAt(pick.id, state.t); if (!p) return null; const e = energyAt(pick.id, state.t);
    return `<b>${pick.id}</b> · ${typeLabel(a)}<br>${STATUS[st] || st} · alt ${Math.round(p[2])} m<br>energie ${Math.round(e)} sur ${Math.round(a.wh)} Wh`; }
  const c = coById[pick.id]; const sv = M.served[pick.id];
  return `<b>${pick.id}</b> · ${reclassAt(pick.id, state.t) ? "reclasse : maintenant ami" : c.cls}${c.points ? "<br>" + c.points + " points" : ""}${Object.keys(c.needs || {}).length ? "<br>besoin de " + Object.entries(c.needs).filter((x) => x[1] > 0).map((x) => x[1] + " " + x[0]).join(", ") : ""}${c.window ? "<br>fenetre " + Math.round(c.window[0]) + "–" + Math.round(c.window[1]) + " s" : ""}${sv !== undefined ? "<br>traite a " + Math.round(sv) + " s" : ""}`;
}
function bindMap() {
  const cv = $("map"); let drag = null;
  cv.addEventListener("wheel", (e) => { e.preventDefault(); orbit.radius = clamp(orbit.radius * Math.exp(e.deltaY * 0.0012), 120, 60000); dirty = true; }, { passive: false });
  cv.addEventListener("pointerdown", (e) => { drag = { x: e.clientX, y: e.clientY, theta: orbit.theta, phi: orbit.phi, tx: orbit.tx, tz: orbit.tz, pan: e.button === 2 || e.shiftKey, moved: false }; cv.setPointerCapture(e.pointerId); cv.classList.add("drag"); });
  cv.addEventListener("contextmenu", (e) => e.preventDefault());
  cv.addEventListener("pointermove", (e) => {
    const r = cv.getBoundingClientRect();
    if (drag) {
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y; if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true;
      if (drag.pan) { const s = orbit.radius * 0.0016; const right = Math.cos(drag.theta), rz = -Math.sin(drag.theta); orbit.tx = drag.tx - (dx * right) * s; orbit.tz = drag.tz - (dx * rz) * s + dy * Math.cos(drag.theta) * s * 0; orbit.tz = drag.tz + dy * Math.sin(drag.theta) * s; orbit.tx = drag.tx - dx * right * s - dy * Math.cos(drag.theta) * s; }
      else { orbit.theta = drag.theta - dx * 0.006; orbit.phi = clamp(drag.phi - dy * 0.006, 0.15, 1.5); }
      dirty = true;
    }
    if (!drag) {
      const pick = pickAt(e.clientX, e.clientY, r);
      const hoverId = pick && pick.kind === "a" ? pick.id : null;
      if (hoverId !== state.hover) { state.hover = hoverId; dirty = true; }
      const tip = $("tip"); const html = hoverInfo(pick);
      if (html) { tip.style.display = "block"; tip.innerHTML = html; const tw = tip.offsetWidth; tip.style.left = Math.min(e.clientX - r.left + 14, r.width - tw - 6) + "px"; tip.style.top = Math.max(e.clientY - r.top - tip.offsetHeight - 8, 4) + "px"; } else tip.style.display = "none";
    }
  });
  cv.addEventListener("pointerup", (e) => { cv.classList.remove("drag"); if (drag && !drag.moved) { const r = cv.getBoundingClientRect(); const pick = pickAt(e.clientX, e.clientY, r); select(pick && pick.kind === "a" ? (pick.id === state.sel ? null : pick.id) : null); } drag = null; });
  cv.addEventListener("pointerleave", () => { $("tip").style.display = "none"; if (state.hover) { state.hover = null; dirty = true; } });
}
function legend() {
  const sw = (cls, txt) => `<span><i style="background:var(--${cls});border-radius:${cls === "civilian" || cls === "scout" ? "50%" : "2px"}"></i>${txt}</span>`;
  $("legend").innerHTML = hasPlan ? `${sw("scout", "eclaireur")}${sw("light", "effecteur leger")}${sw("heavy", "effecteur lourd")}${sw("hostile", "hostile")}${sw("unknown", "inconnu")}${sw("friendly", "ami")}${sw("civilian", "civil")}<span style="color:var(--warn)">○ attente</span>` : `${sw("hostile", "hostile")}${sw("unknown", "inconnu")}${sw("friendly", "ami")}${sw("civilian", "civil")}`;
}
function theme(dark) { state.dark = dark; document.documentElement.setAttribute("data-theme", dark ? "dark" : "light"); try { localStorage.setItem("fleetkit-theme", dark ? "dark" : "light"); } catch (e) { /* no storage */ } if (renderer3) groundColors(); dirty = true; }
function init() {
  let dark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  try { const s = localStorage.getItem("fleetkit-theme"); if (s) dark = s === "dark"; } catch (e) { /* no storage */ }
  theme(dark);
  alertList = buildAlerts();
  $("title").textContent = M.meta.title;
  $("chips").innerHTML = [M.meta.level, "graine " + M.meta.seed, M.aircraft.length + " appareils", W.contacts.length + " contacts", "scene 3D"].map((c) => `<span class="chip">${c}</span>`).join("");
  $("foot-info").textContent = link ? "rejeu perte de liaison" : hasPlan ? "rejeu du plan" : "scenario";
  $("speeds").innerHTML = [1, 2, 4, 8, 16, 32].map((s) => `<button data-s="${s}" class="${s === state.speed ? "on" : ""}">${s}×</button>`).join("");
  $("speeds").onclick = (e) => { const b = e.target.closest("button"); if (!b) return; state.speed = +b.dataset.s; document.querySelectorAll("#speeds button").forEach((x) => x.classList.toggle("on", x === b)); };
  $("play").onclick = togglePlay; $("theme").onclick = () => theme(!state.dark); $("help").onclick = () => { $("modal").hidden = false; }; $("close").onclick = () => { $("modal").hidden = true; };
  $("demo").onclick = runDemo;
  $("modal").onclick = (e) => { if (e.target === $("modal")) $("modal").hidden = true; };
  if (!hasPlan) { $("transport").style.display = "none"; $("alt").style.display = "none"; $("demo").style.display = "none"; }
  buildCard(); buildTabs(); buildPanels(); legend(); bindMap(); bindScrub($("tl"), 8); bindScrub($("alt"), 0);
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT") return; const k = e.key;
    if (k === " ") { e.preventDefault(); togglePlay(); } else if (k === "ArrowRight") setT(state.t + (e.shiftKey ? 10 : 1)); else if (k === "ArrowLeft") setT(state.t - (e.shiftKey ? 10 : 1));
    else if (k === "Home") setT(T0); else if (k === "End") setT(T1); else if (k === "f" || k === "F") fitView(); else if (k === "l" || k === "L") { state.labels = !state.labels; dirty = true; }
    else if (k === "t" || k === "T") theme(!state.dark); else if (k === "Escape") { select(null); $("modal").hidden = true; } else if (k === "?") $("modal").hidden = false;
  });
  window.addEventListener("resize", () => { dirty = true; });
  new ResizeObserver(() => { dirty = true; }).observe($("mapwrap"));
  fitView(); updateClock(); updatePanels();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { dirty = true; });
  window.__viewer = { setT, select, state, orbit, M, fitView, togglePlay, runDemo, draw: () => { dirty = true; }, scene3, camera3, acEntries, contactEntries, posAt, statusAt };
  requestAnimationFrame(frame);
}
init();
})();
