/* global maplibregl */
(function () {
  "use strict";

  // ---------- DOM ----------
  const els = {
    map: document.getElementById("map"),
    loading: document.getElementById("map-loading"),
    stats: document.getElementById("topo-stats"),
    // filters
    fCountry: document.getElementById("filter-country"),
    fRole: document.getElementById("filter-role"),
    fStatus: document.getElementById("filter-status"),
    fIke: document.getElementById("filter-ike_version"),
    fLocation: document.getElementById("filter-location"),
    fDevice: document.getElementById("filter-device"),
    fPlatform: document.getElementById("filter-platform"),
    fScope: document.getElementById("filter-scope"), // optional (internal/external)
    btnApply: document.getElementById("apply-filters"),
    btnReset: document.getElementById("reset-filters"),
    // search / export
    search: document.getElementById("search-nodes"),
    clearSearch: document.getElementById("clear-search"),
    exportPng: document.getElementById("export-png"),
    exportJson: document.getElementById("export-json")
  };

  // ---------- STATE ----------
  const state = {
    map: null,
    mapReady: false,
    sourcesAdded: false,

    // Raw data fetched once (unfiltered)
    fullGraph: null,     // { devices: FC<Point>, tunnels: FC<LineString> }

    // Derived view after client-side filters
    lastGraph: null,     // { devices: FC, tunnels: FC, ha: FC }

    stats: null,         // server-provided or computed
    lastSyncedUTC: "",

    highlightTerm: "",
    didAutoCenterForHighlight: false,
    userInteracting: false
  };

  // ---------- UTIL ----------
  const show = el => { if (el) el.style.display = ""; };
  const hide = el => { if (el) el.style.display = "none"; };
  const val = el => (el && el.value) ? el.value : "";

  function showInfoDialog(lines) {
    const text = Array.isArray(lines) ? lines.filter(Boolean).join("\n") : String(lines || "");
    window.alert(text || "No details available.");
  }

  function orderIndexToOffset(order) {
    if (!order) return 0;
    const step = Math.floor((order + 1) / 2);
    return (order % 2 === 1) ? step : -step;
  }

  function curvedLine(a, b, offsetIndex) {
    if (!Array.isArray(a) || !Array.isArray(b)) return [a, b];
    if (!offsetIndex) return [a, b];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const len = Math.hypot(dx, dy) || 1;
    const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    const normX = -dy / len;
    const normY = dx / len;
    const curveStrength = Math.min(Math.max(len * 0.05, 0.3), 5);
    const magnitude = curveStrength * offsetIndex;
    const midPoint = [mid[0] + normX * magnitude, mid[1] + normY * magnitude];
    return [a, midPoint, b];
  }

  function getJSON(url, params) {
    const full = params ? `${url}?${new URLSearchParams(params)}` : url;
    return fetch(full, { credentials: "same-origin" }).then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status} for ${full}`);
      return r.json();
    });
  }

  function coerceFeatureCollection(maybe) {
    if (!maybe) return { type: "FeatureCollection", features: [] };
    if (maybe.type === "FeatureCollection") return maybe;
    if (Array.isArray(maybe)) return { type: "FeatureCollection", features: maybe };
    if (maybe.features && Array.isArray(maybe.features)) return { type: "FeatureCollection", features: maybe.features };
    return { type: "FeatureCollection", features: [] };
  }

  function makePointFeature(lon, lat, props = {}) {
    return {
      type: "Feature",
      geometry: { type: "Point", coordinates: [Number(lon) || 0, Number(lat) || 0] },
      properties: props
    };
  }

  // quick squared distance (degrees) for nearest endpoint snapping
  function dist2(a, b) {
    const dx = a[0] - b[0];
    const dy = a[1] - b[1];
    return dx * dx + dy * dy;
  }

  function nearestDeviceFeature(coord, deviceFeatures) {
    let best = null;
    let bestD2 = Infinity;
    for (const f of deviceFeatures) {
      const c = f.geometry && f.geometry.coordinates;
      if (!c) continue;
      const d2 = dist2(coord, c);
      if (d2 < bestD2) {
        bestD2 = d2;
        best = f;
      }
    }
    return best;
  }

  // RFC1918 + RFC6598 detection for scope (internal/external)
  function isPrivateIPv4(ip) {
    if (!ip || typeof ip !== "string") return false;
    const m = ip.match(/(\d+)\.(\d+)\.(\d+)\.(\d+)/);
    if (!m) return false;
    const a = +m[1], b = +m[2];
    if (a === 10) return true;
    if (a === 172 && b >= 16 && b <= 31) return true;
    if (a === 192 && b === 168) return true;
    if (a === 100 && b >= 64 && b <= 127) return true; // carrier-grade NAT
    return false;
  }

  function inferScope(props) {
    const s = (props && props.scope) ? String(props.scope).toLowerCase() : "";
    if (s === "internal" || s === "external") return s;
    const li = props && (props.local_ip || props.localIp || props.local);
    const pi = props && (props.peer_ip || props.peerIp || props.peer);
    if (isPrivateIPv4(li) && isPrivateIPv4(pi)) return "internal";
    return "external";
  }

  function fitToDataOnce() {
    if (!state.mapReady || !state.lastGraph) return;
    const pts = state.lastGraph.devices?.features || [];
    const lines = state.lastGraph.tunnels?.features || [];
    if (pts.length === 0 && lines.length === 0) return;

    const bounds = new maplibregl.LngLatBounds();
    pts.forEach(f => f.geometry?.coordinates && bounds.extend(f.geometry.coordinates));
    lines.forEach(f => {
      const coords = f.geometry && f.geometry.coordinates;
      if (Array.isArray(coords)) {
        (f.geometry.type === "LineString" ? [coords] : coords).forEach(line =>
          line.forEach(c => bounds.extend(c))
        );
      }
    });

    if (!bounds.isEmpty()) {
      state.map.stop();
      state.map.fitBounds(bounds, { padding: 50, maxZoom: 4.5, duration: 650 });
    }
  }

  // ---------- HEIGHT: fill remaining viewport ----------
  function setMapHeightToViewport() {
    if (!els.map) return;
    const viewportH = (window.visualViewport?.height || window.innerHeight || 800);
    const top = els.map.getBoundingClientRect().top;
    const padding = 16;
    const h = Math.max(560, Math.floor(viewportH - top - padding));
    els.map.style.height = h + "px";
    if (state.map) state.map.resize();
  }

  // ---------- MAP INIT ----------
  function initMap() {
    if (!els.map) return;

    setMapHeightToViewport();

    const styleUrl = (els.map.dataset.styleUrl || "").trim() ||
      "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
    const attribution = els.map.dataset.attribution || "© OpenStreetMap contributors";
    const initialLat = Number(els.map.dataset.initialLat || 20);
    const initialLon = Number(els.map.dataset.initialLon || 0);
    const initialZoom = Number(els.map.dataset.initialZoom || 1.7);
    const initialPitch = Number(els.map.dataset.initialPitch || 0);
    const initialBearing = Number(els.map.dataset.initialBearing || 0);

    const map = new maplibregl.Map({
      container: els.map,
      style: styleUrl,
      center: [initialLon, initialLat],
      zoom: initialZoom,
      bearing: initialBearing,
      pitch: initialPitch,
      attributionControl: false,
      hash: false,
      preserveDrawingBuffer: true
    });
    state.map = map;

    map.setMinZoom(1.2);
    map.setMaxZoom(18);
    map.addControl(new maplibregl.NavigationControl({ showCompass: true, showZoom: true }), "top-left");
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }));
    map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: attribution }));

    ["movestart", "dragstart", "rotatestart", "pitchstart", "zoomstart"].forEach(evt => {
      map.on(evt, () => { state.userInteracting = true; });
    });

    map.on("load", () => {
      state.mapReady = true;
      addSourcesAndLayers();
      refreshMapSources(); // empty until data arrives
      loadFilters().finally(() => {
        fetchFullGraph().then(() => {
          applyFiltersAndRender(); // initial render
        });
      });
    });

    window.addEventListener("resize", setMapHeightToViewport);
    if (window.visualViewport) window.visualViewport.addEventListener("resize", setMapHeightToViewport);
  }

  // Small helpers to build paint objects we reuse for multiple tunnel layers
  function tunnelWidthPaint() {
    return { "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.6, 6, 1.2, 10, 2.4, 14, 4.0] };
  }
  function tunnelColorPaint() {
    // Color by scope (internal/external). If unknown, fall back to status.
    return {
      "line-color": [
        "case",
        /* internal? */["==", ["downcase", ["coalesce", ["get", "scope"], ""]], "internal"], "#1971c2",
        /* external? */["==", ["downcase", ["coalesce", ["get", "scope"], ""]], "external"], "#2f9e44",
        /* fallback by status */
        ["==", ["downcase", ["coalesce", ["get", "status"], ""]], "failed"], "#e03131",
        ["==", ["downcase", ["coalesce", ["get", "status"], ""]], "planned"], "#f59f00",
        /* default */ "#2f9e44"
      ],
      "line-opacity": 0.9
    };
  }

  // ---------- SOURCES / LAYERS ----------
  function addSourcesAndLayers() {
    if (!state.mapReady || state.sourcesAdded) return;

    state.map.addSource("vpn-devices", { type: "geojson", data: emptyFC() });
    state.map.addSource("vpn-tunnels", { type: "geojson", data: emptyFC() });
    state.map.addSource("vpn-ha-links", { type: "geojson", data: emptyFC() });

    // Devices (points)
    state.map.addLayer({
      id: "vpn-devices",
      type: "circle",
      source: "vpn-devices",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
        "circle-color": [
          "case",
          ["==", ["downcase", ["coalesce", ["get", "status"], ""]], "down"], "#e03131",
          ["==", ["downcase", ["coalesce", ["get", "status"], ""]], "degraded"], "#f59f00",
          /* default */ "#2f9e44"
        ],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 1,
        "circle-opacity": 0.9
      }
    });

    // Highlight (on top)
    state.map.addLayer({
      id: "vpn-devices-highlight",
      type: "circle",
      source: "vpn-devices",
      filter: ["==", ["get", "__highlight"], true],
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 1, 6, 6, 10],
        "circle-color": "#00bcd4",
        "circle-stroke-color": "#003b4a",
        "circle-stroke-width": 2,
        "circle-opacity": 0.95
      }
    });

    // ----- TUNNELS -----
    // We can’t data-drive dasharray in one layer reliably across roles, so use 3 layers.
    // primary (solid), secondary (dashed), tertiary/other (dotted-ish)
    const commonLayout = { "line-cap": "round", "line-join": "round" };

    state.map.addLayer({
      id: "vpn-tunnels-primary",
      type: "line",
      source: "vpn-tunnels",
      filter: ["==", ["downcase", ["coalesce", ["get", "role"], ""]], "primary"],
      layout: commonLayout,
      paint: Object.assign({}, tunnelWidthPaint(), tunnelColorPaint(), { "line-dasharray": [1, 0] })
    });

    state.map.addLayer({
      id: "vpn-tunnels-secondary",
      type: "line",
      source: "vpn-tunnels",
      filter: ["==", ["downcase", ["coalesce", ["get", "role"], ""]], "secondary"],
      layout: commonLayout,
      paint: Object.assign({}, tunnelWidthPaint(), tunnelColorPaint(), { "line-dasharray": [2, 2] })
    });

    state.map.addLayer({
      id: "vpn-tunnels-tertiary",
      type: "line",
      source: "vpn-tunnels",
      filter: ["all",
        ["!=", ["downcase", ["coalesce", ["get", "role"], ""]], "primary"],
        ["!=", ["downcase", ["coalesce", ["get", "role"], ""]], "secondary"]
      ],
      layout: commonLayout,
      // dotted effect (short round dashes)
      paint: Object.assign({}, tunnelWidthPaint(), tunnelColorPaint(), { "line-dasharray": [0.5, 1.5] })
    });

    // Tunnel labels (better contrast)
    state.map.addLayer({
      id: "vpn-tunnel-labels",
      type: "symbol",
      source: "vpn-tunnels",
      layout: {
        "symbol-placement": "line-center",
        "text-field": ["coalesce", ["get", "name"], ""],
        "text-size": 11,
        "text-optional": true
      },
      paint: {
        "text-color": "#22306f",
        "text-halo-width": 1.2,
        "text-halo-color": "rgba(255,255,255,0.95)"
      }
    });

    // HA links (dashed purple)
    state.map.addLayer({
      id: "vpn-ha-lines",
      type: "line",
      source: "vpn-ha-links",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": "#b197fc",
        "line-width": 2,
        "line-dasharray": [2, 2],
        "line-opacity": 0.8
      }
    });

    // ---------- POPUPS ----------
    const hoverPop = new maplibregl.Popup({ closeButton: false, closeOnClick: false, maxWidth: "320px" });

    // Device hover -> tooltip
    state.map.on("mousemove", "vpn-devices", (e) => {
      const f = e.features && e.features[0]; if (!f) return;
      state.map.getCanvas().style.cursor = "pointer";
      const p = f.properties || {};
      const name = p.name || p.device || p.hostname || "Device";
      const status = p.status || "unknown";
      const platform = p.platform || "";
      hoverPop.setLngLat(e.lngLat)
        .setHTML(
          `<div style="font-weight:600">${name}</div>` +
          `<div>Status: ${status}${platform ? ` · ${platform}` : ""}</div>`
        ).addTo(state.map);
    });
    state.map.on("mouseleave", "vpn-devices", () => {
      state.map.getCanvas().style.cursor = "";
      hoverPop.remove();
    });

    // Device click -> alert dialog
    state.map.on("click", "vpn-devices", (e) => {
      const f = e.features && e.features[0]; if (!f) return;
      hoverPop.remove();
      const p = f.properties || {};
      const name = p.name || p.device || p.hostname || "Device";
      const status = p.status || "unknown";
      const platform = p.platform || "";
      const role = p.role || "";
      const country = p.country || "";
      const location = p.location || "";
      const lines = [
        `Device: ${name}`,
        `Status: ${status}`,
        platform ? `Platform: ${platform}` : "",
        role ? `Role: ${role}` : "",
        country ? `Country: ${country}` : "",
        location ? `Location: ${location}` : ""
      ];
      showInfoDialog(lines);
    });

    // Tunnel hover -> light tooltip (quick glance)
    ["vpn-tunnels-primary", "vpn-tunnels-secondary", "vpn-tunnels-tertiary"].forEach(layerId => {
      state.map.on("mousemove", layerId, (e) => {
        const f = e.features && e.features[0]; if (!f) return;
        state.map.getCanvas().style.cursor = "pointer";
        const p = f.properties || {};
        const name = p.name || "Tunnel";
        const status = p.status || "";
        const ike = p.ike_version || p.ike || "";
        const scope = (p.scope || "").toString().toLowerCase();
        hoverPop.setLngLat(e.lngLat)
          .setHTML(
            `<div style="font-weight:600">${name}</div>` +
            (status ? `<div>Status: ${status}${ike ? ` · IKE ${ike}` : ""}</div>` : (ike ? `<div>IKE ${ike}</div>` : "")) +
            (scope ? `<div>Scope: ${scope}</div>` : "")
          ).addTo(state.map);
      });
      state.map.on("mouseleave", layerId, () => {
        state.map.getCanvas().style.cursor = "";
        hoverPop.remove();
      });
    });

    // Tunnel click -> alert dialog (tooltip_details_json if present)
    ["vpn-tunnels-primary", "vpn-tunnels-secondary", "vpn-tunnels-tertiary"].forEach(layerId => {
      state.map.on("click", layerId, (e) => {
        const f = e.features && e.features[0]; if (!f) return;
        hoverPop.remove();
        const p = f.properties || {};
        let lines = [];

        if (p.tooltip) {
          try {
            const obj = (typeof p.tooltip === "string") ? JSON.parse(p.tooltip) : p.tooltip;
            if (obj && typeof obj === "object") {
              lines = Object.entries(obj).map(([k, v]) => `${k}: ${v ?? ""}`);
            }
          } catch { /* ignore and fallback */ }
        }
        if (!lines.length) {
          const name = p.name || "Tunnel";
          const status = p.status || "Unknown";
          const role = p.role || "";
          const ike = p.ike_version || p.ike || "";
          const lip = p.local_ip || "";
          const pip = p.peer_ip || "";
          const scope = (p.scope || "").toString().toLowerCase();
          lines = [
            `Tunnel: ${name}`,
            `Status: ${status}${role ? ` · ${role}` : ""}${ike ? ` · IKE ${ike}` : ""}`,
            scope ? `Scope: ${scope}` : "",
            lip ? `Local IP: ${lip}` : "",
            pip ? `Peer IP: ${pip}` : ""
          ];
        }
        showInfoDialog(lines);
      });
    });

    state.sourcesAdded = true;
  }

  function emptyFC() { return { type: "FeatureCollection", features: [] }; }

  // ---------- STATS (badge strip) ----------
  function renderStatsLine() {
    if (!els.stats) return;

    const d = state.lastGraph?.devices?.features || [];

    const meta = state.meta || {};
    const statusCounts = meta.status_counts || {};
    const statusLabels = meta.status_labels || {};
    const preferredStatusOrder = ["active", "down", "decommissioned", "disabled", "planned"];
    const statusOrder = [...new Set([
      ...preferredStatusOrder,
      ...(Array.isArray(meta.status_order) ? meta.status_order.map(s => String(s).toLowerCase()) : []),
      ...Object.keys(statusCounts)
    ])];
    const statusIcons = {
      active: "🟢",
      down: "🔻",
      failed: "🔴",
      planned: "🟡",
      disabled: "⛔",
      decommissioned: "🗑️",
    };
    const statusSegments = [];
    statusOrder.forEach(slug => {
      const count = statusCounts[slug] ?? 0;
      const mustShow = preferredStatusOrder.includes(slug);
      if (!mustShow && !count) return;
      const icon = statusIcons[slug] || "⚪";
      const label = statusLabels[slug]
        || slug.replace(/[_-]/g, " ").replace(/\b\w/g, ch => ch.toUpperCase());
      statusSegments.push(`${icon} ${count} ${label}`);
    });

    const totalTunnels = meta.total_tunnels ?? meta.tunnels_count ?? (state.lastGraph?.tunnels?.features?.length || 0);

    const roleCounts = meta.role_counts || {};
    const roleLabels = meta.role_labels || {};
    const preferredRoleOrder = ["primary", "secondary", "tertiary"];
    const roleOrder = [...new Set([
      ...preferredRoleOrder,
      ...(Array.isArray(meta.role_order) ? meta.role_order.map(s => String(s).toLowerCase()) : []),
      ...Object.keys(roleCounts)
    ])];
    const roleIcons = { primary: "🎯", secondary: "🔁", tertiary: "🧭", unassigned: "⚪" };
    const roleSegments = [];
    roleOrder.forEach(slug => {
      const count = roleCounts[slug] ?? 0;
      const mustShow = preferredRoleOrder.includes(slug);
      if (!mustShow && !count) return;
      const icon = roleIcons[slug] || "⚪";
      const label = roleLabels[slug]
        || slug.replace(/[_-]/g, " ").replace(/\b\w/g, ch => ch.toUpperCase());
      roleSegments.push(`${icon} ${count} ${label}`);
    });

    const devicesCount = meta.devices_count ?? d.length;
    const countries = meta.countries_count ?? new Set(d.map(f => f.properties?.country).filter(Boolean)).size;
    const platforms = meta.platforms_count ?? new Set(d.map(f => f.properties?.platform).filter(Boolean)).size;

    const haPairs = (() => {
      if (meta.ha_pairs != null) return Number(meta.ha_pairs);
      const dedup = new Set();
      const idx = new Map(d.map(f => [String(f.properties?.id), f]));
      d.forEach(f => {
        const me = String(f.properties?.id || "");
        const peer = String(f.properties?.ha_peer_id || "");
        if (me && peer && idx.has(peer)) dedup.add([me, peer].sort().join("-"));
      });
      return dedup.size;
    })();

    let lastSynced = meta.last_synced || state.lastSyncedUTC || "";
    if (lastSynced) {
      const dt = new Date(lastSynced);
      if (!Number.isNaN(dt.getTime())) {
        const pad = n => String(n).padStart(2, "0");
        lastSynced = `${dt.getUTCFullYear()}-${pad(dt.getUTCMonth() + 1)}-${pad(dt.getUTCDate())} ` +
          `${pad(dt.getUTCHours())}:${pad(dt.getUTCMinutes())}:${pad(dt.getUTCSeconds())} UTC`;
      } else {
        lastSynced = String(lastSynced);
      }
    }

    const segments = [
      ...statusSegments,
      `🔗 ${totalTunnels} Tunnels`,
      ...roleSegments,
      `🖥️ ${devicesCount} Devices (${countries} Countries, ${platforms} Platforms)`,
    ];
    if (haPairs) segments.push(`🟪 ${haPairs} HA pairs`);
    if (lastSynced) segments.push(`⏱ Last synced at: ${lastSynced}`);
    if (meta.last_sync_status) segments.push(`📋 Sync status: ${meta.last_sync_status}`);

    els.stats.innerHTML = (devicesCount + totalTunnels === 0)
      ? "No devices found for selected filters."
      : segments.filter(Boolean).join(" | ");
  }

  function refreshMapSources() {
    if (!state.mapReady) return;
    const devSrc = state.map.getSource("vpn-devices");
    const tunSrc = state.map.getSource("vpn-tunnels");
    const haSrc = state.map.getSource("vpn-ha-links");

    if (devSrc) devSrc.setData(state.lastGraph?.devices || emptyFC());
    if (tunSrc) tunSrc.setData(state.lastGraph?.tunnels || emptyFC());
    if (haSrc) haSrc.setData(state.lastGraph?.ha || emptyFC());

    renderStatsLine();
  }

  // ---------- DATA / FILTERS ----------
  function option(el, value, label) {
    const o = document.createElement("option");
    o.value = value; o.textContent = label;
    el.appendChild(o);
  }

  function loadFilters() {
    return getJSON("/api/plugins/nautobot_app_vpn/v1/topology-filters/").then(data => {
      const d = data || {};
      [
        [els.fCountry, d.country],
        [els.fRole, d.role],
        [els.fStatus, d.status],
        [els.fIke, d.ike_version],
        [els.fLocation, d.location],
        [els.fDevice, d.device],
        [els.fPlatform, d.platform]
      ].forEach(([sel, arr]) => {
        if (!sel) return;
        if (Array.isArray(arr)) arr.forEach(v => option(sel, String(v), String(v)));
      });

    // Optional scope filter values (internal/external)
    if (els.fScope && els.fScope.options.length <= 1) {
        ["", "internal", "external"].forEach(v => option(els.fScope, v, v ? v[0].toUpperCase() + v.slice(1) : "All Scopes"));
    }
    }).catch(() => { /* non-fatal */ });
  }

  function collectFilters() {
    return {
      country: val(els.fCountry),
      role: val(els.fRole),
      status: val(els.fStatus),
      ike_version: val(els.fIke),
      location: val(els.fLocation),
      device: val(els.fDevice),
      platform: val(els.fPlatform),
      scope: val(els.fScope),
      search: (els.search && els.search.value) ? els.search.value.trim() : ""
    };
  }

  // Fetch unfiltered once; we’ll filter client-side so peer endpoints remain visible.
  function fetchFullGraph() {
    show(els.loading);
    return getJSON("/api/plugins/nautobot_app_vpn/v1/topology-neo4j/", null)
      .then((payload) => {
        let devFC = coerceFeatureCollection(payload?.devices);
        let tunFC = coerceFeatureCollection(payload?.tunnels);

        // Accept flat arrays too (lon/lat on each device object)
        if (devFC.features.length === 0 && Array.isArray(payload?.devices)) {
          devFC = {
            type: "FeatureCollection",
            features: payload.devices
              .filter((d) => d && d.lon != null && d.lat != null)
              .map((d) => makePointFeature(d.lon, d.lat, d)),
          };
        }

        state.fullGraph = { devices: devFC, tunnels: tunFC };
        state.stats = payload?.stats || null;
        state.meta = payload?.meta || null;
        state.lastSyncedUTC = payload?.last_synced || payload?.meta?.last_synced || "";

        renderStatsLine();
      })
      .catch((err) => {
        console.error("Failed to load topology:", err);
        state.fullGraph = { devices: emptyFC(), tunnels: emptyFC() };
        state.stats = null;
        state.lastSyncedUTC = "";
        renderStatsLine();
      })
      .finally(() => hide(els.loading));
  }

  // Apply UI filters, keeping tunnels that match edge filters AND touch matched devices.
  function applyFiltersAndRender() {
    if (!state.fullGraph) {
      state.lastGraph = { devices: emptyFC(), tunnels: emptyFC(), ha: emptyFC() };
      refreshMapSources();
      return;
    }

    const filters = collectFilters();
    const devAll = state.fullGraph.devices.features;
    const tunAll = state.fullGraph.tunnels.features;

    const eq = (a, b) => String(a ?? "").toLowerCase() === String(b ?? "").toLowerCase();
    const contains = (a, b) => String(a ?? "").toLowerCase().includes(String(b ?? "").toLowerCase());

    // Device property match
    const matchesDevice = (p) => {
      if (!p) return false;
      const countryOk = !filters.country || eq(p.country, filters.country);
      const platformOk = !filters.platform || eq(p.platform, filters.platform);
      const statusOk = !filters.status || eq(p.status, filters.status);
      const locationOk = !filters.location || eq(p.location, filters.location);
      const roleOk = !filters.role ||
        eq(p.role, filters.role) || eq(p.ha_role, filters.role) || eq(p.ha_state, filters.role);

      const deviceOk = !filters.device || (() => {
        const sel = String(filters.device).trim();
        if (!sel) return true;
        const selLow = sel.toLowerCase();
        if (String(p.id) === sel) return true;
        if (eq(p.name, sel) || eq(p.device, sel) || eq(p.hostname, sel)) return true;
        const names = Array.isArray(p.device_names) ? p.device_names : [];
        const pks = Array.isArray(p.nautobot_device_pks) ? p.nautobot_device_pks.map(String) : [];
        if (names.some(n => eq(n, sel))) return true;
        if (names.some(n => String(n || "").toLowerCase().includes(selLow))) return true; // partial match for HA
        if (pks.some(pk => pk === sel)) return true;
        return false;
      })();

      const term = (filters.search || "").trim().toLowerCase();
      const searchOk = !term ||
        contains(p.name, term) || contains(p.device, term) || contains(p.hostname, term) || contains(p.search_text, term) ||
        contains(p.firewall_hostnames, term) ||
        (Array.isArray(p.device_names) && p.device_names.some(n => contains(n, term)));

      return countryOk && roleOk && platformOk && deviceOk && statusOk && locationOk && searchOk;
    };

    // Seed with devices that match UI
    const matchedDevices = devAll.filter(f => matchesDevice(f.properties));

    // Highlight matching devices for search
    const term = (filters.search || "").trim().toLowerCase();
    if (term) {
      matchedDevices.forEach(f => {
        const p = f.properties || {};
        const hay = (p.name || p.device || p.hostname || "").toString().toLowerCase();
        const extra = (p.search_text || "").toString().toLowerCase();
        f.properties.__highlight = (hay.includes(term) || extra.includes(term));
      });
    } else {
      devAll.forEach(f => { if (f.properties) f.properties.__highlight = false; });
    }

    // Build tunnel subset
    const deviceFeatures = devAll;

    const edgeMatchesEdgeFilters = (p) => {
      if (!p) return false;
      // role/status/ike only filter if a value is provided in UI
      const roleOk = !filters.role || eq(p.role, filters.role);
      const statusOk = !filters.status || eq(p.status, filters.status);
      const ikeOk = !filters.ike_version || eq(p.ike_version || p.ike, filters.ike_version);
      const scope = inferScope(p);
      const scopeOk = !filters.scope || eq(scope, filters.scope);
      return roleOk && statusOk && ikeOk && scopeOk;
    };

    const matchedIds = new Set(matchedDevices.map(f => String(f.properties?.id)));

    function endpointsForTunnel(tunnelFeature) {
      const coords = tunnelFeature?.geometry?.coordinates || [];
      const a = coords && coords[0], b = coords && coords[coords.length - 1];
      const fa = a ? nearestDeviceFeature(a, deviceFeatures) : null;
      const fb = b ? nearestDeviceFeature(b, deviceFeatures) : null;
      return { fa, fb };
    }

    const keptTunnels = tunAll.filter(t => {
      const p = t.properties || {};
      if (!edgeMatchesEdgeFilters(p)) return false;

      const anyDeviceFilter = !!(filters.country || filters.platform || filters.location || filters.device || filters.search);
      if (!anyDeviceFilter) return true;

      const { fa, fb } = endpointsForTunnel(t);
      const aId = fa && String(fa.properties?.id);
      const bId = fb && String(fb.properties?.id);
      if ((aId && matchedIds.has(aId)) || (bId && matchedIds.has(bId))) return true;
      // Fallback: match by endpoint names provided in edge properties (if available)
      if (filters.device) {
        const dev = String(filters.device).toLowerCase();
        const hosts = String(p.firewall_hostnames || "").toLowerCase();
        if (dev && hosts.includes(dev)) return true;
      }
      return false;
    });

    const pairBuckets = new Map();

    // Collect devices that are endpoints of kept tunnels
    const allowIds = new Set();
    keptTunnels.forEach(t => {
      const { fa, fb } = endpointsForTunnel(t);
      if (fa) allowIds.add(String(fa.properties?.id));
      if (fb) allowIds.add(String(fb.properties?.id));
      if (!fa || !fb) return;

      const aProps = fa.properties || {};
      const bProps = fb.properties || {};
      const pairKey = [String(aProps.id), String(bProps.id)].sort().join("||");
      if (!pairBuckets.has(pairKey)) {
        pairBuckets.set(pairKey, []);
      }
      pairBuckets.get(pairKey).push({
        tunnel: t,
        props: t.properties || {},
        fa,
        fb,
        aProps,
        bProps,
      });
    });

    // If nothing matched and no filters -> show everything
    const nothingFiltered = Object.values(filters).every(v => !v);
    if (nothingFiltered) devAll.forEach(f => allowIds.add(String(f.properties?.id)));

    const keptDevices = devAll.filter(f => allowIds.has(String(f.properties?.id)));

    // Build tunnel features with role-aware ordering and offsets
    const idx = new Map(keptDevices.map(f => [String(f.properties?.id), f]));
    const normalizeRole = role => {
      const val = (role || "").toString().toLowerCase();
      if (!val) return "unassigned";
      if (val === "primary" || val === "secondary" || val === "tertiary") return val;
      return val;
    };
    const rolePriorityOrder = ["primary", "secondary", "tertiary"];
    const roleBaseOffset = { primary: 0, secondary: 1.5, tertiary: -1.5, unassigned: 3 };
    const defaultBaseOffset = 3.5;
    const duplicateSpacing = 0.8;

    const tunnelsFeatures = [];

    pairBuckets.forEach(bucket => {
      bucket.forEach(item => {
        item.roleKey = normalizeRole(item.props.role);
      });

      bucket.sort((a, b) => {
        const priA = rolePriorityOrder.includes(a.roleKey) ? rolePriorityOrder.indexOf(a.roleKey) : rolePriorityOrder.length;
        const priB = rolePriorityOrder.includes(b.roleKey) ? rolePriorityOrder.indexOf(b.roleKey) : rolePriorityOrder.length;
        if (priA !== priB) return priA - priB;
        const nameA = (a.props.name || "").toString();
        const nameB = (b.props.name || "").toString();
        return nameA.localeCompare(nameB);
      });

      const perRoleCounts = {};

      bucket.forEach(item => {
        const roleKey = item.roleKey;
        const aCoord = item.fa.geometry && item.fa.geometry.coordinates;
        const bCoord = item.fb.geometry && item.fb.geometry.coordinates;
        if (!Array.isArray(aCoord) || !Array.isArray(bCoord)) return;

        const name = item.props.name
          || `${item.aProps.name || item.aProps.device || "A"} ⇄ ${item.bProps.name || item.bProps.device || "B"}`;
        const scope = inferScope(item.props);

        const roleIndex = perRoleCounts[roleKey] || 0;
        perRoleCounts[roleKey] = roleIndex + 1;

        const base = Object.prototype.hasOwnProperty.call(roleBaseOffset, roleKey)
          ? roleBaseOffset[roleKey]
          : defaultBaseOffset;
        const extra = orderIndexToOffset(roleIndex) * duplicateSpacing;
        const offsetIdx = Math.max(Math.min(base + extra, 6), -6);
        const arcCoords = curvedLine(aCoord, bCoord, offsetIdx);

        tunnelsFeatures.push({
          type: "Feature",
          geometry: { type: "LineString", coordinates: arcCoords },
          properties: {
            id: item.props.id || `${item.aProps.id}-${item.bProps.id}`,
            name,
            src: item.aProps.name || item.aProps.device || "",
            dst: item.bProps.name || item.bProps.device || "",
            status: item.props.status || "active",
            ike_version: item.props.ike_version || item.props.ike || "",
            role: roleKey,
            local_ip: item.props.local_ip || "",
            peer_ip: item.props.peer_ip || "",
            scope,
            firewall_hostnames: item.props.firewall_hostnames || "",
            offset_index: offsetIdx,
            tooltip: item.props.tooltip || "",
          }
        });
      });
    });

    const tunnelsFC = {
      type: "FeatureCollection",
      features: tunnelsFeatures
    };

    // HA links (dedup)
    const haSeen = new Set();
    const haFeats = [];
    keptDevices.forEach(f => {
      const p = f.properties || {};
      const me = String(p.id || "");
      const peerId = String(p.ha_peer_id || "");
      if (!me || !peerId) return;
      const peer = idx.get(peerId);
      if (!peer) return;
      const key = [me, peerId].sort().join("-");
      if (haSeen.has(key)) return;
      haSeen.add(key);
      haFeats.push({
        type: "Feature",
        properties: { a: p.name || p.device || me, b: peer.properties?.name || peer.properties?.device || peerId },
        geometry: { type: "LineString", coordinates: [f.geometry.coordinates, peer.geometry.coordinates] }
      });
    });

    state.lastGraph = {
      devices: { type: "FeatureCollection", features: keptDevices },
      tunnels: tunnelsFC,
      ha: { type: "FeatureCollection", features: haFeats }
    };

    applySearchHighlight(state.highlightTerm || "");
    refreshMapSources();
    if (!state.userInteracting) fitToDataOnce();
  }

  // ---------- SEARCH / HIGHLIGHT ----------
  function applySearchHighlight(term) {
    state.highlightTerm = term;
    state.didAutoCenterForHighlight = false;

    const normalized = (term || "").trim().toLowerCase();
    const devs = state.lastGraph?.devices?.features || [];
    devs.forEach(f => {
      const p = f.properties || {};
      const hay = (p.name || p.device || p.hostname || "").toString().toLowerCase();
      const extra = (p.search_text || "").toString().toLowerCase();
      const fw = (p.firewall_hostnames || "").toString().toLowerCase();
      f.properties.__highlight = !!normalized && (hay.includes(normalized) || extra.includes(normalized) || fw.includes(normalized));
    });

    refreshMapSources();

    if (normalized && !state.didAutoCenterForHighlight && !state.userInteracting && devs.length) {
      const match = devs.find(f => f.properties.__highlight);
      if (match && state.mapReady) {
        state.didAutoCenterForHighlight = true;
        state.map.stop();
        state.map.easeTo({
          center: match.geometry.coordinates,
          duration: 600,
          zoom: Math.max(state.map.getZoom(), 3.5)
        });
      }
    }
  }

  // ---------- EXPORTS ----------
  function exportPNG() {
    if (!state.mapReady) return;
    try { const m = state.map; m && m.resize(); } catch {}
    const link = document.createElement("a");
    link.href = state.map.getCanvas().toDataURL("image/png");
    link.download = "vpn_map.png";
    link.click();
  }

  function exportJSON() {
    const blob = new Blob([JSON.stringify(state.lastGraph || {}, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vpn_topology.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  // (Removed 4K exporter by request)

  // ---------- EVENTS ----------
  function wireUI() {
    if (els.btnApply) {
      els.btnApply.addEventListener("click", () => {
        state.userInteracting = false; // allow fit after new filters
        applyFiltersAndRender();
      });
    }
    if (els.btnReset) {
      els.btnReset.addEventListener("click", () => {
        const selects = [els.fCountry, els.fRole, els.fStatus, els.fIke, els.fLocation, els.fDevice, els.fPlatform, els.fScope];
        selects.forEach(el => {
          if (!el) return;
          if (window.jQuery && window.$ && $(el).select2) {
            $(el).val(null).trigger("change");
          } else {
            el.value = "";
            el.dispatchEvent(new Event("change"));
          }
        });
        if (els.search) els.search.value = "";
        state.userInteracting = false;
        state.highlightTerm = "";
        applyFiltersAndRender();
      });
    }
    if (els.search) {
      els.search.addEventListener("input", (e) => applySearchHighlight(e.target.value || ""));
    }
    if (els.clearSearch) {
      els.clearSearch.addEventListener("click", () => {
        if (els.search) els.search.value = "";
        applySearchHighlight("");
      });
    }
    if (els.exportPng) els.exportPng.addEventListener("click", exportPNG);
    if (els.exportJson) els.exportJson.addEventListener("click", exportJSON);
  }

  // ---------- BOOT ----------
  function emptyOr(value, fallback) { return (value == null ? fallback : value); }
  wireUI();
  initMap();

  // Optional hook to push new data live
  window.__vpnTopologyUpdate = function (payload) {
    let devFC = coerceFeatureCollection(payload?.devices);
    let tunFC = coerceFeatureCollection(payload?.tunnels);
    if (devFC.features.length === 0 && Array.isArray(payload?.devices)) {
      devFC = {
        type: "FeatureCollection",
        features: payload.devices
          .filter(d => d && d.lon != null && d.lat != null)
          .map(d => makePointFeature(d.lon, d.lat, d))
      };
    }
    state.fullGraph = { devices: devFC, tunnels: tunFC };
    state.stats = payload?.stats || null;
    state.meta = payload?.meta || state.meta;
    state.lastSyncedUTC = emptyOr(payload?.last_synced || payload?.meta?.last_synced, state.lastSyncedUTC);
    applyFiltersAndRender();
  };
})();
