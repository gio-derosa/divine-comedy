(function () {
  "use strict";

  var CANTICHE = [
    { name: "Inferno", cantos: 34 },
    { name: "Purgatorio", cantos: 33 },
    { name: "Paradiso", cantos: 33 }
  ];

  // Each tab reads only its own source file.
  var TABS = {
    it: {
      file: "data/petrocchi.js", global: "DC_PETROCCHI",
      lang: "it", translationLang: "en",
      canto: "Canto",
      hint: "Tocca un verso per vederne la traduzione letterale.",
      loading: "Caricamento…",
      darkMode: "Tema scuro"
    },
    en: {
      file: "data/longfellow.js", global: "DC_LONGFELLOW",
      lang: "en", translationLang: "it",
      canto: "Canto",
      hint: "Tap a line to see its literal Italian translation.",
      loading: "Loading…",
      darkMode: "Dark mode"
    }
  };

  var state = { tab: "it", cantica: "Inferno", canto: 1 };
  var loaded = {};    // tab -> Promise of data
  var flipped = {};   // "tab|cantica|canto" -> { lineNumber: true } for lines showing their translation

  var $ = function (sel) { return document.querySelector(sel); };
  var $$ = function (sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); };

  function roman(n) {
    var map = [[50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]];
    var out = "";
    map.forEach(function (p) { while (n >= p[0]) { out += p[1]; n -= p[0]; } });
    return out;
  }

  function canticaInfo(name) {
    for (var i = 0; i < CANTICHE.length; i++) if (CANTICHE[i].name === name) return CANTICHE[i];
    return null;
  }

  // Global order of all 100 cantos, for previous/next across cantica boundaries.
  var ORDER = [];
  CANTICHE.forEach(function (c) {
    for (var n = 1; n <= c.cantos; n++) ORDER.push({ cantica: c.name, canto: n });
  });
  function orderIndex() {
    for (var i = 0; i < ORDER.length; i++) {
      if (ORDER[i].cantica === state.cantica && ORDER[i].canto === state.canto) return i;
    }
    return 0;
  }

  function loadTab(tab) {
    if (!loaded[tab]) {
      var cfg = TABS[tab];
      loaded[tab] = new Promise(function (resolve, reject) {
        if (window[cfg.global]) return resolve(window[cfg.global]);
        var s = document.createElement("script");
        s.src = cfg.file;
        s.onload = function () { resolve(window[cfg.global]); };
        s.onerror = function () { delete loaded[tab]; reject(new Error("Could not load " + cfg.file)); };
        document.head.appendChild(s);
      });
    }
    return loaded[tab];
  }

  // ---- URL hash: #it/inferno/1 ----
  function readHash() {
    var parts = location.hash.replace(/^#\/?/, "").split("/");
    var tab = TABS[parts[0]] ? parts[0] : state.tab;
    var cantica = null;
    CANTICHE.forEach(function (c) { if (c.name.toLowerCase() === (parts[1] || "").toLowerCase()) cantica = c; });
    cantica = cantica || canticaInfo(state.cantica);
    var canto = parseInt(parts[2], 10);
    if (!(canto >= 1 && canto <= cantica.cantos)) canto = parts[1] ? 1 : state.canto;
    state.tab = tab; state.cantica = cantica.name; state.canto = canto;
  }
  function writeHash() {
    var h = "#" + state.tab + "/" + state.cantica.toLowerCase() + "/" + state.canto;
    if (location.hash !== h) history.replaceState(null, "", h);
  }

  // ---- Rendering ----
  function renderControls() {
    var cfg = TABS[state.tab];
    document.documentElement.lang = cfg.lang;
    $$(".tabs button").forEach(function (b) {
      var on = b.getAttribute("data-lang") === state.tab;
      b.setAttribute("aria-selected", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
    });
    $$(".cantiche button").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-cantica") === state.cantica ? "true" : "false");
    });

    var sel = $("#canto-select");
    var info = canticaInfo(state.cantica);
    sel.innerHTML = "";
    for (var n = 1; n <= info.cantos; n++) {
      var o = document.createElement("option");
      o.value = n;
      o.textContent = cfg.canto + " " + roman(n);
      sel.appendChild(o);
    }
    sel.value = state.canto;

    var i = orderIndex();
    var prev = ORDER[i - 1], next = ORDER[i + 1];
    $$(".prev").forEach(function (b) { b.disabled = !prev; });
    $$(".next").forEach(function (b) { b.disabled = !next; });
    $(".bottom-nav .prev span").textContent = prev ? prev.cantica + " " + roman(prev.canto) : "";
    $(".bottom-nav .next span").textContent = next ? next.cantica + " " + roman(next.canto) : "";

    $("#canto-title").textContent = state.cantica + " · " + cfg.canto + " " + roman(state.canto);
    $("#hint").textContent = cfg.hint;
    $(".theme-toggle").setAttribute("aria-label", cfg.darkMode);
    $(".theme-toggle").title = cfg.darkMode;
    document.title = state.cantica + " " + roman(state.canto) + " · La Divina Commedia";
  }

  function flipKey() { return state.tab + "|" + state.cantica + "|" + state.canto; }

  function setLine(el, line, showTranslation) {
    var cfg = TABS[state.tab];
    var text = el.querySelector(".text");
    text.textContent = showTranslation ? line[1] : line[0];
    text.lang = showTranslation ? cfg.translationLang : cfg.lang;
    el.classList.toggle("is-translation", showTranslation);
    el.setAttribute("aria-pressed", showTranslation ? "true" : "false");
  }

  function renderPoem(data) {
    var poem = $("#poem");
    var lines = data[state.cantica][state.canto - 1];
    var flips = flipped[flipKey()] || (flipped[flipKey()] = {});
    var frag = document.createDocumentFragment();
    var tercet;
    lines.forEach(function (line, idx) {
      var n = idx + 1;
      if (idx % 3 === 0) {
        tercet = document.createElement("div");
        tercet.className = "tercet";
        frag.appendChild(tercet);
      }
      var p = document.createElement("p");
      p.className = "line";
      p.tabIndex = 0;
      p.setAttribute("role", "button");
      p.setAttribute("data-n", n);
      if (n % 3 === 0) {
        var num = document.createElement("span");
        num.className = "num";
        num.setAttribute("aria-hidden", "true");
        num.textContent = n;
        p.appendChild(num);
      }
      if (line[2]) {
        // Label placed before the text so it never wraps onto a line by itself.
        var tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = line[2];
        p.appendChild(tag);
      }
      var text = document.createElement("span");
      text.className = "text";
      p.appendChild(text);
      setLine(p, line, !!flips[n]);
      tercet.appendChild(p);
    });
    poem.innerHTML = "";
    poem.appendChild(frag);
  }

  var renderToken = 0;
  function render(scroll) {
    renderControls();
    writeHash();
    var token = ++renderToken;
    var poem = $("#poem");
    if (!window[TABS[state.tab].global]) {
      poem.innerHTML = '<p class="loading">' + TABS[state.tab].loading + "</p>";
    }
    loadTab(state.tab).then(function (data) {
      if (token !== renderToken) return;  // a newer navigation superseded this one
      renderPoem(data);
      if (scroll) window.scrollTo(0, 0);
    }, function (err) {
      if (token !== renderToken) return;
      poem.innerHTML = '<p class="error"></p>';
      poem.firstChild.textContent = err.message;
    });
  }

  function go(cantica, canto) {
    state.cantica = cantica;
    state.canto = canto;
    render(true);
  }
  function step(delta) {
    var target = ORDER[orderIndex() + delta];
    if (target) go(target.cantica, target.canto);
  }

  // ---- Theme ----
  // Follows the system setting until the reader picks one; the choice is remembered.
  var systemDark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  function isDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return !!(systemDark && systemDark.matches);
  }
  function syncThemeButton() {
    $(".theme-toggle").setAttribute("aria-pressed", isDark() ? "true" : "false");
  }
  $(".theme-toggle").addEventListener("click", function () {
    var t = isDark() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem("theme", t); } catch (e) {}
    syncThemeButton();
  });
  if (systemDark && systemDark.addEventListener) systemDark.addEventListener("change", syncThemeButton);
  syncThemeButton();

  // ---- Events ----
  function toggleLine(el) {
    var n = parseInt(el.getAttribute("data-n"), 10);
    var flips = flipped[flipKey()];
    flips[n] = !flips[n];
    // Lines only exist once their tab's data has loaded, so it is safe to read directly.
    var data = window[TABS[state.tab].global];
    setLine(el, data[state.cantica][state.canto - 1][n - 1], flips[n]);
  }

  $("#poem").addEventListener("click", function (e) {
    if (window.getSelection && String(window.getSelection()).length) return;  // allow selecting text
    var el = e.target.closest(".line");
    if (el) toggleLine(el);
  });
  $("#poem").addEventListener("keydown", function (e) {
    var el = e.target.closest && e.target.closest(".line");
    if (el && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      toggleLine(el);
    }
  });

  $$(".tabs button").forEach(function (b) {
    b.addEventListener("click", function () {
      state.tab = b.getAttribute("data-lang");
      render(false);
    });
  });
  $(".tabs").addEventListener("keydown", function (e) {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    state.tab = state.tab === "it" ? "en" : "it";
    render(false);
    $("#tab-" + state.tab).focus();
  });
  $$(".cantiche button").forEach(function (b) {
    b.addEventListener("click", function () {
      var c = b.getAttribute("data-cantica");
      if (c !== state.cantica) go(c, 1);
    });
  });
  $("#canto-select").addEventListener("change", function (e) {
    go(state.cantica, parseInt(e.target.value, 10));
  });
  $$(".prev").forEach(function (b) { b.addEventListener("click", function () { step(-1); }); });
  $$(".next").forEach(function (b) { b.addEventListener("click", function () { step(1); }); });

  window.addEventListener("hashchange", function () { readHash(); render(true); });

  readHash();
  render(false);
})();
