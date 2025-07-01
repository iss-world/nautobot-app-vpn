/**
 * Advanced Cytoscape loader (Promise-based, extensible).
 * Loads Cytoscape.js + KLAY layout (with fallback to COSE), plus optional extra extensions.
 * Fires a 'cytoscape:loaded' event on success.
 * @param {Function} [callback] Optional callback support
 * @param {string[]} [extraExtensions] URLs for additional Cytoscape extensions to load (optional)
 * @returns {Promise<void>}
 */
function loadCytoscape(callback, extraExtensions = []) {
  if (window.cytoscape && cytoscape.extensions?.layout?.klay) {
    callback?.();
    document.dispatchEvent(new CustomEvent('cytoscape:loaded'));
    return Promise.resolve();
  }
  if (window.__cytoscape_loading__) {
    return window.__cytoscape_loading__.then(() => { callback?.(); });
  }
  let resolveLoader, rejectLoader;
  window.__cytoscape_loading__ = new Promise((resolve, reject) => {
    resolveLoader = resolve; rejectLoader = reject;
  });

  function loadScript(url) {
    return new Promise((resolve, reject) => {
      const el = document.createElement("script");
      el.src = url;
      el.async = true;
      el.onload = resolve;
      el.onerror = reject;
      document.head.appendChild(el);
    });
  }


  // Chain loading: cytoscape, KLAY, any extras
  let loader = loadScript("https://unpkg.com/cytoscape@3.24.0/dist/cytoscape.min.js")
    .then(() => loadScript("https://unpkg.com/cytoscape-klay@3.1.4/cytoscape-klay.js"));
  for (const ext of extraExtensions) {
    loader = loader.then(() => loadScript(ext));
  }
  loader.then(() => {
    try {
      const klayExt = window.cytoscapeKlay || window.klay;
      if (klayExt) {
        cytoscape.use(klayExt);
        console.info("✅ KLAY extension registered successfully.");
      } else {
        console.warn("⚠️ KLAY extension not found, will fallback to COSE layout.");
      }
    } catch (e) {
      console.error("❌ Failed to register KLAY:", e);
    }
    resolveLoader();
    callback?.();
    document.dispatchEvent(new CustomEvent('cytoscape:loaded'));
  })
  .catch(err => {
    // Fallback to COSE only
    console.warn("⚠️ Failed to load Cytoscape/KLAY, only basic Cytoscape (COSE) will work.", err);
    resolveLoader(); // Still resolve so the app continues
    callback?.();
    document.dispatchEvent(new CustomEvent('cytoscape:loaded'));
  });

  return window.__cytoscape_loading__;
}


function transformPositionToCurrentViewport(x, y, svgWidth, svgHeight, cyWidth, cyHeight) {
  // Scale to fit container. Assume 0,0 is top-left.
  const scaleX = cyWidth / svgWidth;
  const scaleY = cyHeight / svgHeight;
  return {
    x: x * scaleX,
    y: y * scaleY
  };
}

// Topology dashboard init after Cytoscape/KLAY is loaded
loadCytoscape(() => {
  const cy = cytoscape({
    container: document.getElementById("cy"),
    elements: [],
    style: [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "text-valign": "bottom",
          "text-halign": "center",
          color: "#000",
          "font-size": 8,
          "text-margin-y": 6,
          "text-wrap": "wrap",
          "background-color": "#ccc",
          "background-fit": "cover",
          "border-width": 2,
          "border-color": "#000"
        }
      },
      {
        selector: "edge",
        style: {
          label: "data(label)",
          "curve-style": "bezier",
          "target-arrow-shape": "triangle",
          "target-arrow-color": "#888",
          "line-color": "#888",
          width: 1,
          "font-size": 6,
          "text-background-opacity": 1,
          "text-background-color": "#fff",
          "text-background-padding": 2,
          "text-rotation": "autorotate"
        }
      }
    ],
    layout: { name: "preset" }
  });

  // --- Filters
  const filterFields = ["country", "role", "status", "ike_version", "location", "device", "platform"];
  const FILTER_STORAGE_KEY = "cy_dashboard_filters_v1";

  // Save current filters to localStorage
  function saveFilters() {
    const state = {};
    filterFields.forEach(f => {
      const el = document.getElementById(`filter-${f}`);
      state[f] = el?.value ?? "";
    });
    localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(state));
  }

  // Restore filters from localStorage
  function restoreFilters() {
    try {
      const state = JSON.parse(localStorage.getItem(FILTER_STORAGE_KEY) || "{}");
      filterFields.forEach(f => {
        const el = document.getElementById(`filter-${f}`);
        if (el && typeof state[f] === "string") el.value = state[f];
      });
    } catch {}
  }

  function buildQuery() {
    return filterFields
      .map(f => {
        const el = document.getElementById(`filter-${f}`);
        const v = el?.value?.trim();
        return v ? `${f}=${encodeURIComponent(v)}` : "";
      })
      .filter(Boolean)
      .join("&");
  }

  // Filter population with Select2 + Promise + de-duplication + accessibility
  function fetchFiltersFromAPI() {
    return fetch("/api/plugins/nautobot_app_vpn/v1/topology-filters/")
      .then(r => {
        if (!r.ok) throw new Error("Failed to fetch filter options");
        return r.json();
      })
      .then(filters => {
        const pluralKeys = {
          country: "countries",
          role: "roles",
          status: "statuses",
          ike_version: "ike_versions",
          device: "devices",
          location: "locations",
          platform: "platforms"
        };
        filterFields.forEach(field => {
          const el = document.getElementById(`filter-${field}`);
          if (!el) return;
          const key = pluralKeys[field] || field;
          let values = filters[key] || [];

          // Remove duplicates (by label or value)
          if (typeof values[0] === "object" && values[0] !== null) {
            const seen = new Set();
            values = values.filter(v => {
              // Use unique primary key or label/name, fallback to full object
              const uniq = (typeof v.id !== "undefined") ? v.id
                : (typeof v.label !== "undefined") ? v.label
                : (typeof v.name !== "undefined") ? v.name
                : JSON.stringify(v);
              if (seen.has(uniq)) return false;
              seen.add(uniq);
              return true;
            });
          } else {
            values = [...new Set(values)];
          }

          // Default "All" option
          el.innerHTML = `<option value="">All ${field.charAt(0).toUpperCase() + field.slice(1)}</option>`;

          for (const v of values) {
            const opt = document.createElement("option");
            opt.setAttribute("aria-label", `Filter by ${field}`);

            if (field === "device" && typeof v === "object" && v.id) {
              opt.value = v.id;
              opt.textContent = v.label || v.id;
            } else if (field === "platform" && typeof v === "object" && v.name) {
              opt.value = v.id;
              opt.textContent = v.name;
            } else if (typeof v === "object" && v.label) {
              opt.value = v.label;
              opt.textContent = v.label;
            } else if (typeof v === "object" && v.name) {
              opt.value = v.name;
              opt.textContent = v.name;
            } else {
              opt.value = v;
              opt.textContent = v;
            }
            el.appendChild(opt);
          }

          // Re-initialize Select2 if present
          if (window.jQuery && window.jQuery(el).select2) {
            window.jQuery(el).select2({ width: "resolve" });
          }
        });
        restoreFilters(); // Restore filters after options are set
      })
      .catch(err => {
        console.error("❌ Could not load filter options:", err);
        // Optionally: show a toast or error banner to user here
      });
  }

  // --- Save filter state on change
  filterFields.forEach(f => {
    const el = document.getElementById(`filter-${f}`);
    if (el) {
      el.addEventListener("change", saveFilters);
    }
  });

  // Export for use in main UI logic
  window.__cy_dashboard__ = { cy, filterFields, buildQuery, fetchFiltersFromAPI, saveFilters, restoreFilters };

  function fetchDataAndRender() {
    document.body.style.cursor = "wait";
    const loadingEl = document.getElementById("cy-loading");
    if (loadingEl) loadingEl.style.display = "block";
    const statEl = document.getElementById("topo-stats");
    if (statEl) statEl.textContent = "Loading topology…";

    // Save current filters
    if (window.__cy_dashboard__?.saveFilters) window.__cy_dashboard__.saveFilters();

    const query = buildQuery();
    const url = "/api/plugins/nautobot_app_vpn/v1/topology-neo4j/" + (query ? `?${query}` : "");

    // Optional: Save pan/zoom to restore after re-draw
    const lastPan = cy.pan();
    const lastZoom = cy.zoom();

    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error(`Failed to fetch: ${r.status}`);
        return r.json();
      })
      .then(data => {
        cy.elements().remove();

        // Defensive: If no nodes, show user
        if (!data.nodes?.length) {
          if (statEl) statEl.textContent = "No nodes found for selected filters.";
          cy.resize();
          return;
        }

        // ===== Map native SVG to viewport before adding nodes =====
        const svgWidth = 2754;
        const svgHeight = 1398;
        const cyWidth = cy.width();
        const cyHeight = cy.height();

        data.nodes.forEach(node => {
          if (
            node.position &&
            typeof node.position.x === "number" &&
            typeof node.position.y === "number"
          ) {
            const { x, y } = transformPositionToCurrentViewport(
              node.position.x,
              node.position.y,
              svgWidth,
              svgHeight,
              cyWidth,
              cyHeight
            );
            node.position.x = x;
            node.position.y = y;
          }
        });
        // =========================================================

        // Add and animate elements
        cy.add(data.nodes || []);
        cy.add(data.edges || []);
        const focusIds = new Set((data.meta?.focus_node_ids || []).map(String));
        cy.nodes().forEach(n => {
          if (focusIds.has(n.data('id'))) {
            n.addClass('cy-focus');
          } else {
            n.removeClass('cy-focus');
          }
        });


        // Animate fade-in
        cy.batch(() => {
          cy.nodes().forEach(n => n.style("opacity", 0.1));
          cy.edges().forEach(e => e.style("opacity", 0.1));
        });
        setTimeout(() => {
          cy.nodes().forEach(n => n.style("opacity", 1));
          cy.edges().forEach(e => e.style("opacity", 1));
        }, 250);

        // --- Node Styling & Tooltips ---
        cy.nodes().forEach(node => {
          const icon = node.data("icon_filename");
          const country = node.data("country") || "N/A";
          const isHA = !!node.data("is_ha_pair");
          const isManual = !!node.data("is_manual_peer");
          const platform = (node.data("platform_name") || "").trim();

          node.style("border-color", isHA ? "#ff00ff" : "#000");
          node.style("border-width", isHA ? 4 : 2);

          if (isManual) {
            node.style("shape", "round-rectangle");
            node.style("background-color", "#cccccc");
            if (!platform || platform.toLowerCase() === "unknown") {
              // If peer platform is NOT set, use unknown.svg
              node.style("background-image", "/static/nautobot_app_vpn/img/unknown.svg");
            } else if (icon && icon !== "unknown.svg") {
              // If peer platform is set and icon is meaningful, use its icon
              node.style("background-image", "/static/nautobot_app_vpn/img/" + icon);
            } else {
              node.style("background-image", "");
            }
            node.style("background-fit", "cover");
          } else if (icon && icon !== "unknown.svg") {
            node.style("background-image", "/static/nautobot_app_vpn/img/" + icon);
            node.style("background-fit", "cover");
            node.style("background-color", "#fff");
          } else {
            node.style("background-image", "");
            node.style("background-color", "#bbb");
          }

          // Tooltip data
          let tooltip = node.data("label") || "";
          tooltip += `\nPlatform: ${node.data("platform_name") || ""}`;
          tooltip += `\nIP: ${node.data("primary_ip") || ""}`;
          tooltip += `\nCountry: ${country}`;
          tooltip += `\nLocation: ${node.data("location_name") || ""}`;
          tooltip += `\nStatus: ${node.data("status") || ""}`;
          if (isHA) tooltip += "\n(HA Pair)";
          if (isManual && node.data("location_name"))
            tooltip += `\nManual Location: ${node.data("location_name")}`;
          node.data("tooltip", tooltip);
        });

        // --- Edge Styling ---
        cy.edges().forEach(edge => {
          const status = (edge.data("status") || "").toLowerCase();
          let color = "#999";
          if (status === "active") color = "#28a745";
          else if (status === "planned") color = "#ffc107";
          else if (["failed", "down"].includes(status)) color = "#dc3545";
          edge.style("line-color", color);
          edge.style("target-arrow-color", color);
        });

        // --- Layout Logic ---
        let preset = cy.nodes().some(n => n.position("x") !== undefined && n.position("y") !== undefined);
        let layout = preset ? "preset" : (cytoscape.extensions?.layout?.klay ? "klay" : "cose");
        cy.layout({
          name: layout,
          animate: true,
          ...(layout === "klay" ? {
            klay: {
              direction: "RIGHT",
              spacing: 70,
              nodePlacement: "LINEAR",
              edgeRouting: "ORTHOGONAL",
              thoroughness: 50,
              aspectRatio: 1.5
            }
          } : {})
        }).run();

        // Restore pan/zoom after redraw
        cy.pan(lastPan);
        cy.zoom(lastZoom);

        // --- Stats bar & extra meta ---
        if (data.meta) {
          const active = data.meta.active_tunnels_shown || 0;
          const failed = data.meta.failed_tunnels_shown || 0;
          const planned = data.meta.planned_tunnels_shown || 0;
          const total = data.meta.total_edges_shown || 0;
          const nodes = data.meta.total_nodes_shown || data.nodes?.length || 0;
          const ha = data.meta.ha_pairs_shown || 0;
          const uniqueCountries = new Set((data.nodes || []).map(n => n.data.country).filter(Boolean)).size;
          const uniquePlatforms = new Set((data.nodes || []).map(n => n.data.platform_name).filter(Boolean)).size;

          const stats = `
            🟢 ${active} Active |
            🔴 ${failed} Failed |
            🟡 ${planned} Planned |
            🔗 ${total} Tunnels |
            🖥️ ${nodes} Devices (${uniqueCountries} Countries, ${uniquePlatforms} Platforms)${ha ? ` | 🟪 ${ha} HA pairs` : ""}
          `.replace(/\s+/g, " ").trim();

          const syncTime = data.meta.last_synced_at
            ? `⏱ Last synced at: ${new Date(data.meta.last_synced_at).toLocaleString("en-GB", { timeZone: "UTC" })} UTC`
            : "⏱ Last synced at: —";

          if (statEl) statEl.textContent = `${stats} | ${syncTime}`;
        }
      })
      .catch(err => {
        const errorMsg = "❌ Failed to load topology. See console for details.";
        if (statEl) statEl.textContent = errorMsg;
        if (window.Toastify) {
          Toastify({ text: errorMsg, backgroundColor: "red", duration: 3500 }).showToast();
        } else {
          alert(errorMsg);
        }
        console.error("Topology fetch failed:", err);
        cy.elements().remove();
      })
      .finally(() => {
        document.body.style.cursor = "default";
        if (loadingEl) loadingEl.style.display = "none";
      });
  }


  // --- Filter Application and Reset ---
  document.getElementById("apply-filters")?.addEventListener("click", fetchDataAndRender);

  document.getElementById("reset-filters")?.addEventListener("click", () => {
    filterFields.forEach(f => {
      const el = document.getElementById(`filter-${f}`);
      if (el) el.value = "";
      // If using Select2 or similar, also call: $(el).val('').trigger('change');
    });
    fetchDataAndRender();
  });

  // --- Edge Click: Show Details in Modal, Toast, or Alert ---
  cy.on("tap", "edge", evt => {
    // Try to get the tooltip details as JSON string first
    let tooltipDetails = evt.target.data("tooltip_details_json");
    if (tooltipDetails && typeof tooltipDetails === "string") {
      try {
        tooltipDetails = JSON.parse(tooltipDetails);
      } catch (e) {
        // fallback if malformed
        tooltipDetails = null;
      }
    } else if (evt.target.data("tooltip_details") && typeof evt.target.data("tooltip_details") === "object") {
      // (Legacy or local use) - handle as before
      tooltipDetails = evt.target.data("tooltip_details");
    }

    let msg = "No tunnel info.";
    if (tooltipDetails && typeof tooltipDetails === "object") {
      msg = Object.entries(tooltipDetails)
        .filter(([k, v]) => v && v !== "N/A")
        .map(([k, v]) => `${k}: ${v}`)
        .join("\n");
    } else if (evt.target.data("tooltip")) {
      msg = evt.target.data("tooltip");
    }

    // Use your preferred display (Toastify or alert)
    if (window.Toastify) {
      Toastify({ text: msg, duration: 6000, gravity: "top", backgroundColor: "#222" }).showToast();
    } else {
      alert(msg);
    }
  });

  // --- Node Search: Fuzzy Filtering, Highlights ---
  document.getElementById("search-nodes")?.addEventListener("input", e => {
    const term = e.target.value.toLowerCase();

    cy.elements().forEach(el => {
      // Try node‐label first; if it’s an edge, fall back to edge‐label (or any other field)
      const label =
        (el.data("label")?.toLowerCase()) || ""; // adjust if your edges use a different key
      const visible = !term || label.includes(term);
      el.style("opacity", visible ? 1 : 0.2);
    });
  });

  // --- Search Reset ---
  document.getElementById("clear-search")?.addEventListener("click", () => {
    const input = document.getElementById("search-nodes");
    if (input) input.value = "";

    cy.elements().forEach(el => {
      el.style("opacity", 1);
    });
  });
  
  // --- Export as PNG (full canvas snapshot) ---
  document.getElementById("export-png")?.addEventListener("click", () => {
    const png = cy.png({ full: true, bg: "#ffffff" });
    const a = document.createElement("a");
    a.href = png;
    a.download = `vpn_topology_${new Date().toISOString().replace(/[-:.TZ]/g, "")}.png`;
    a.click();
  });

  // --- Export as JSON (full graph state) ---
  document.getElementById("export-json")?.addEventListener("click", () => {
    const json = JSON.stringify(cy.json(), null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `vpn_topology_${new Date().toISOString().replace(/[-:.TZ]/g, "")}.json`;
    a.click();
  });

  // --- Initial load ---
  fetchFiltersFromAPI();
  fetchDataAndRender();

  // Optional: Listen for window resize and force Cytoscape resize
  window.addEventListener("resize", () => {
    cy.resize();
  });
});