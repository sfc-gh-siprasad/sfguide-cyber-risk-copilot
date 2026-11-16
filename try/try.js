// Hosted no-install example. Reads window.CYBER_DATA from data.js (synthetic).
(function () {
  "use strict";
  var D = window.CYBER_DATA;
  var SVG = "http://www.w3.org/2000/svg";
  var COLORS = { Critical: "var(--c1)", High: "var(--c2)", Medium: "var(--c4)", Low: "var(--c3)" };

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (text !== undefined && text !== null) n.textContent = text;
    return n;
  }
  function svg(tag, attrs) {
    var n = document.createElementNS(SVG, tag);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    return n;
  }
  function niceMax(v) { return Math.ceil(v / 100) * 100 || 100; }
  function fmt(n) { return Number(n).toLocaleString("en-US"); }
  function pct(x) { return (x * 100).toFixed(1) + "%"; }

  // Render **bold** markdown only; everything else stays plain text (no HTML injection).
  function richText(parent, text) {
    String(text).split(/(\*\*[^*]+\*\*)/).forEach(function (part) {
      if (/^\*\*[^*]+\*\*$/.test(part)) parent.appendChild(el("strong", {}, part.slice(2, -2)));
      else if (part) parent.appendChild(document.createTextNode(part));
    });
  }

  function legend(parent, items) {
    var l = el("div", { class: "legend" });
    items.forEach(function (it) {
      var s = el("span");
      var sw = el("i"); sw.style.background = it.color;
      s.appendChild(sw); s.appendChild(document.createTextNode(it.label));
      l.appendChild(s);
    });
    parent.appendChild(l);
  }

  // Vertical bar chart: groups[] of { label, values: [{key, value}] }, stacked or side by side.
  function barChart(target, groups, keys, colors, stacked, desc) {
    var W = 520, H = 230, P = { l: 36, r: 8, t: 10, b: 40 };
    var max = 0;
    groups.forEach(function (g) {
      var vals = keys.map(function (k) { return g.values[k] || 0; });
      max = Math.max(max, stacked ? vals.reduce(function (a, b) { return a + b; }, 0) : Math.max.apply(null, vals));
    });
    max = niceMax(max);
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": desc });
    for (var t = 0; t <= 4; t++) {
      var v = max * t / 4, y = P.t + (H - P.t - P.b) * (1 - t / 4);
      s.appendChild(svg("line", { x1: P.l, x2: W - P.r, y1: y, y2: y, stroke: "var(--border)" }));
      var tx = svg("text", { x: P.l - 6, y: y + 4, "text-anchor": "end" }); tx.textContent = Math.round(v); s.appendChild(tx);
    }
    var band = (W - P.l - P.r) / groups.length;
    groups.forEach(function (g, i) {
      var x0 = P.l + band * i + band * 0.15, bw = band * 0.7, acc = 0;
      keys.forEach(function (k, j) {
        var v = g.values[k] || 0, h = (H - P.t - P.b) * v / max;
        var x = stacked ? x0 : x0 + (bw / keys.length) * j, w = stacked ? bw : bw / keys.length - 2;
        var y = H - P.b - h - (stacked ? acc : 0);
        var r = svg("rect", { x: x, y: y, width: Math.max(w, 1), height: h, fill: colors[j] });
        var tt = svg("title"); tt.textContent = g.label + " · " + k + ": " + v; r.appendChild(tt);
        s.appendChild(r);
        if (stacked) acc += h;
      });
      var lb = svg("text", { x: x0 + bw / 2, y: H - P.b + 16, "text-anchor": "middle" }); lb.textContent = g.label; s.appendChild(lb);
    });
    target.appendChild(s);
    legend(target, keys.map(function (k, j) { return { label: k, color: colors[j] }; }));
  }

  function lineChart(target, rows, keys, colors, desc) {
    var W = 520, H = 230, P = { l: 36, r: 8, t: 10, b: 40 };
    var max = 0;
    rows.forEach(function (r) { keys.forEach(function (k) { max = Math.max(max, r[k]); }); });
    max = niceMax(max);
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": desc });
    for (var t = 0; t <= 4; t++) {
      var y = P.t + (H - P.t - P.b) * (1 - t / 4);
      s.appendChild(svg("line", { x1: P.l, x2: W - P.r, y1: y, y2: y, stroke: "var(--border)" }));
      var tx = svg("text", { x: P.l - 6, y: y + 4, "text-anchor": "end" }); tx.textContent = Math.round(max * t / 4); s.appendChild(tx);
    }
    var step = (W - P.l - P.r) / (rows.length - 1);
    function px(i) { return P.l + step * i; }
    function py(v) { return H - P.b - (H - P.t - P.b) * v / max; }
    keys.forEach(function (k, j) {
      var d = rows.map(function (r, i) { return (i ? "L" : "M") + px(i) + " " + py(r[k]); }).join(" ");
      s.appendChild(svg("path", { d: d, fill: "none", stroke: colors[j], "stroke-width": 2.2 }));
    });
    rows.forEach(function (r, i) {
      if (i % 3) return;
      var lb = svg("text", { x: px(i), y: H - P.b + 16, "text-anchor": "middle" }); lb.textContent = r.month.split(" ")[0]; s.appendChild(lb);
    });
    target.appendChild(s);
    legend(target, keys.map(function (k, j) { return { label: k, color: colors[j] }; }));
  }

  // cols: [{ key, label, num?, render? }]
  function table(t, rows, cols) {
    t.textContent = "";
    var thead = el("thead"), tr = el("tr");
    cols.forEach(function (c) { tr.appendChild(el("th", c.num ? { class: "num", scope: "col" } : { scope: "col" }, c.label)); });
    thead.appendChild(tr); t.appendChild(thead);
    var tb = el("tbody");
    rows.forEach(function (r) {
      var row = el("tr");
      cols.forEach(function (c) {
        var td = el("td", c.num ? { class: "num" } : {});
        if (c.render) c.render(td, r[c.key], r); else td.textContent = r[c.key] === null ? "" : r[c.key];
        row.appendChild(td);
      });
      tb.appendChild(row);
    });
    t.appendChild(tb);
  }
  function rateCell(td, v) {
    var b = el("span", { class: "bar" }); b.style.width = Math.round(v * 60) + "px";
    td.appendChild(b); td.appendChild(document.createTextNode(pct(v)));
  }
  function flag(td, v) { td.textContent = v ? "Yes" : "No"; }

  // ---------- overview ----------
  document.querySelectorAll("[data-asof]").forEach(function (n) { n.textContent = D.asOf; });
  var k = D.kpis;
  [["Open findings", fmt(k.open_findings)], ["Open critical", fmt(k.open_critical)],
   ["SLA breach rate", pct(k.sla_breach_rate)], ["Average open age", Math.round(k.avg_open_age_days) + " days"],
   ["Internet-facing, open", fmt(k.internet_facing_open)], ["Known exploited, open", fmt(k.known_exploited_open)]
  ].forEach(function (p) {
    var c = el("div", { class: "kpi" }); c.appendChild(el("span", {}, p[0])); c.appendChild(el("strong", {}, p[1]));
    document.getElementById("kpis").appendChild(c);
  });

  barChart(document.getElementById("chart-severity"),
    D.severity.map(function (r) { return { label: r.severity, values: { Open: r.open_findings, Overdue: r.overdue } }; }),
    ["Open", "Overdue"], ["var(--c1)", "var(--c2)"], false, "Open and overdue findings by severity");

  lineChart(document.getElementById("chart-trend"), D.trend, ["Opened", "Resolved"], ["var(--c1)", "var(--c2)"],
    "Findings opened and resolved per month over the last 12 months");

  var buckets = [], byBucket = {};
  D.aging.forEach(function (r) {
    if (!byBucket[r.bucket]) { byBucket[r.bucket] = {}; buckets.push(r.bucket); }
    byBucket[r.bucket][r.severity] = r["Open findings"];
  });
  var sevs = ["Critical", "High", "Medium", "Low"];
  barChart(document.getElementById("chart-aging"),
    buckets.map(function (b) { return { label: b, values: byBucket[b] }; }),
    sevs, sevs.map(function (s) { return COLORS[s]; }), true, "Open findings by age bucket and severity");

  table(document.getElementById("top-services"), D.services.slice(0, 8), [
    { key: "service_name", label: "Service" }, { key: "tier", label: "Tier", num: true },
    { key: "open_critical", label: "Open critical", num: true }, { key: "overdue", label: "Overdue", num: true },
    { key: "sla_breach_rate", label: "SLA breach rate", render: rateCell }]);

  // ---------- services ----------
  var tiers = { 1: true, 2: true, 3: true };
  var tierBox = document.getElementById("tier-filters");
  [1, 2, 3].forEach(function (t) {
    var b = el("button", { class: "chip", "aria-pressed": "true", type: "button" }, "Tier " + t);
    b.addEventListener("click", function () {
      tiers[t] = !tiers[t]; b.setAttribute("aria-pressed", String(tiers[t])); renderServices();
    });
    tierBox.appendChild(b);
  });
  var pick = document.getElementById("service-pick");
  pick.addEventListener("change", renderPriority);

  function renderServices() {
    var rows = D.services.filter(function (r) { return tiers[r.tier]; });
    table(document.getElementById("service-table"), rows, [
      { key: "service_name", label: "Service" }, { key: "tier", label: "Tier", num: true },
      { key: "line_of_business", label: "Line of business" }, { key: "team_name", label: "Owning team" },
      { key: "open_findings", label: "Open", num: true }, { key: "open_critical", label: "Critical", num: true },
      { key: "overdue", label: "Overdue", num: true },
      { key: "avg_age_days", label: "Avg age (days)", num: true, render: function (td, v) { td.textContent = Math.round(v); } },
      { key: "sla_breach_rate", label: "SLA breach rate", render: rateCell }]);
    var current = pick.value;
    pick.textContent = "";
    rows.forEach(function (r) { pick.appendChild(el("option", { value: r.service_name }, r.service_name)); });
    if (rows.some(function (r) { return r.service_name === current; })) pick.value = current;
    renderPriority();
  }
  function renderPriority() {
    var name = pick.value;
    document.getElementById("priority-title").textContent = name ? "Highest-priority open findings: " + name : "No services match the filters";
    table(document.getElementById("priority-table"), name ? D.priority[name] : [], [
      { key: "finding_id", label: "Finding" }, { key: "title", label: "Title" }, { key: "severity", label: "Severity" },
      { key: "asset_name", label: "Asset" }, { key: "internet_facing", label: "Internet-facing", render: flag },
      { key: "known_exploited", label: "Known exploited", render: flag }, { key: "due_date", label: "Due" },
      { key: "team_name", label: "Owner" }, { key: "priority_score", label: "Priority score", num: true }]);
  }
  renderServices();

  // ---------- copilot ----------
  var chat = document.getElementById("chat"), sugg = document.getElementById("suggestions");
  function ask(q) {
    var u = el("div", { class: "msg user" }, q); chat.appendChild(u);
    var a = D.answers[q], m = el("div", { class: "msg bot" });
    var p = el("p"); richText(p, a.answer); m.appendChild(p);
    m.appendChild(el("span", { class: "label" }, "Sample AI response"));
    if (a.table && a.table.length) {
      var wrap = el("div", { class: "scroll" }), t = el("table");
      var keys = Object.keys(a.table[0]);
      table(t, a.table, keys.map(function (kk) {
        return { key: kk, label: kk.replace(/_/g, " "), num: typeof a.table[0][kk] === "number",
                 render: kk === "sla_breach_rate" ? function (td, v) { td.textContent = pct(v); } : null };
      }));
      wrap.appendChild(t); m.appendChild(wrap);
    }
    (a.sources || []).forEach(function (s) {
      var d = el("div", { class: "src" }); d.appendChild(el("strong", {}, s.title)); d.appendChild(el("p", {}, s.text)); m.appendChild(d);
    });
    chat.appendChild(m);
    m.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  D.questions.forEach(function (q) {
    var b = el("button", { type: "button" }, q);
    b.addEventListener("click", function () { ask(q); });
    sugg.appendChild(b);
  });

  // ---------- navigation ----------
  function show(id) {
    document.querySelectorAll(".page").forEach(function (p) { p.hidden = p.id !== id; });
    document.querySelectorAll(".nav").forEach(function (b) {
      var on = b.getAttribute("data-page") === id;
      b.classList.toggle("active", on);
      if (on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  }
  document.querySelectorAll(".nav").forEach(function (b) {
    b.addEventListener("click", function () { show(b.getAttribute("data-page")); });
  });
  var start = location.hash.slice(1);
  show(["overview", "services", "copilot"].indexOf(start) >= 0 ? start : "overview");
})();
