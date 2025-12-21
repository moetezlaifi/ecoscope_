// CONFIGURATION INITIALE
const map = L.map('map', { zoomControl: false }).setView([36.0, 9.5], 7);

// Fond de carte clair "Positron"
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO'
}).addTo(map);

let currentMode = 'hydro';
let markers = [];

// Fallback demo data (only used if API fails)
const demoSites = [
    {
        id: 1, name: "Oued Meliane", lat: 36.75, lon: 10.28, type: "Embouchure Oued",
        hydroRisk: 92, bioRisk: 30,
        hydroFactors: { "Accumulation Plastique": 94, "Prévision Pluie": 65, "Ruissellement": 70 },
        bioFactors: { "Stress NDVI": 55, "Stress Chaleur": 20, "Extrême Pluie": 30 }
    },
];

// Will be replaced by API results
let sites = [];

/**
 * Convert API record -> UI site object (keeps same design).
 * Expected API item shape:
 * {
 *   name, lat, lon,
 *   water_risk, bio_risk,
 *   explain: { water: {...}, bio: {...} }
 * }
 */
function apiToSite(item, idx) {
    const waterRisk = Math.round(Number(item.water_risk ?? 0));
    const bioRisk = Math.round(Number(item.bio_risk ?? 0));

    const ex = item.explain || {};
    const w = ex.water || {};
    const b = ex.bio || {};

    // Hydro factors: top 3 strongest coefficients OR show main features as percents
    // We convert coefficients to readable percent weights (hackathon-friendly)
    const imp = w.feature_importance || {};
    const sortedDrivers = Object.entries(imp)
        .sort((a, bb) => Math.abs(bb[1]) - Math.abs(a[1]))
        .slice(0, 3);

    const hydroFactors = {};
    if (sortedDrivers.length) {
        // Normalize to 0..100 for UI bars
        const mags = sortedDrivers.map(([k, v]) => Math.abs(Number(v) || 0));
        const sum = mags.reduce((a, c) => a + c, 0) || 1;
        sortedDrivers.forEach(([k, v], i) => {
            const pct = Math.round((Math.abs(Number(v) || 0) / sum) * 100);
            hydroFactors[k.replaceAll("_", " ")] = pct;
        });
    } else {
        // Fallback from features
        hydroFactors["Plastique"] = Math.round((w.features?.plastic_score ?? 0) * 100);
        hydroFactors["Pluie 24h"] = Math.min(100, Math.round((w.features?.rain_mm_24 ?? 0) * 3));
        hydroFactors["NDVI"] = Math.round((w.features?.ndvi ?? 0) * 100);
    }

    // Bio factors: directly from components 0..1 → 0..100
    const comp = b.components || {};
    const bioFactors = {
        "Stress NDVI": Math.round((Number(comp.ndvi_stress) || 0) * 100),
        "Stress Chaleur": Math.round((Number(comp.heat_stress) || 0) * 100),
        "Extrême Pluie": Math.round((Number(comp.rain_extreme) || 0) * 100),
    };

    return {
        id: idx + 1,
        name: item.name || `Site ${idx + 1}`,
        lat: Number(item.lat),
        lon: Number(item.lon),
        type: "Site Surveillé",
        hydroRisk: waterRisk,
        bioRisk: bioRisk,
        hydroFactors,
        bioFactors,
        rawExplain: ex,
    };
}

async function loadSitesFromAPI() {
    const res = await fetch("/api/risk?h=24");
    if (!res.ok) throw new Error("API /api/risk failed");
    const data = await res.json();
    return data.map(apiToSite);
}

// SWITCH MODES
function switchMode(mode) {
    currentMode = mode;
    const btnH = document.getElementById('btn-hydro');
    const btnB = document.getElementById('btn-bio');

    if (mode === 'hydro') {
        btnH.className = "px-5 py-1.5 rounded-full text-xs font-bold transition-all bg-emerald-600 text-white shadow-md";
        btnB.className = "px-5 py-1.5 rounded-full text-xs font-bold transition-all text-slate-500 hover:text-slate-800";
    } else {
        btnB.className = "px-5 py-1.5 rounded-full text-xs font-bold transition-all bg-blue-600 text-white shadow-md";
        btnH.className = "px-5 py-1.5 rounded-full text-xs font-bold transition-all text-slate-500 hover:text-slate-800";
    }
    if (typeof updateChartTheme === "function") {
        updateChartTheme(mode);
    }
    renderApp();
}

// RENDU DE LA CARTE ET DE LA SIDEBAR
function renderApp() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    const container = document.getElementById('alerts-container');
    container.innerHTML = '';

    // Global status
    const global = document.getElementById("global-status");
    const modeLabel = currentMode === "hydro" ? "HydroScope (Eau)" : "BioScope (Biodiversité)";
    global.textContent = `Mode: ${modeLabel} • ${sites.length} sites chargés. Cliquez sur un point pour les détails.`;

    sites.forEach(site => {
        const risk = currentMode === 'hydro' ? site.hydroRisk : site.bioRisk;
        const color = risk > 75 ? '#ef4444' : (risk > 45 ? '#f59e0b' : '#10b981');

        // Icône personnalisée avec clignotement fixe si risque > 75%
        const icon = L.divIcon({
            html: `<div class="${risk > 75 ? 'pulse-red' : ''}" style="width:14px; height:14px; background-color:${color}; border:2px solid white; border-radius:50%; box-shadow:0 2px 4px rgba(0,0,0,0.1);"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7]
        });

        const marker = L.marker([site.lat, site.lon], { icon: icon }).addTo(map);
        marker.on('click', () => showDetails(site));
        markers.push(marker);

        // Ajout à la sidebar si risque significatif
        if (risk > 50) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `p-4 rounded-2xl border transition-all shadow-lg ${risk > 75 ? 'border-red-100' : 'border-orange-100'} bg-white/80 hover:bg-white cursor-pointer`;
            alertDiv.onclick = () => showDetails(site);

            alertDiv.innerHTML = `
                <div class="flex justify-between items-start mb-1">
                    <span class="text-[9px] font-black uppercase tracking-widest ${risk > 75 ? 'text-red-500' : 'text-orange-500'}">${risk > 75 ? 'CRITIQUE' : 'ALERTE'}</span>
                    <span class="text-[10px] font-black text-slate-800">${risk}%</span>
                </div>
                <div class="text-sm font-black tracking-tight">${site.name}</div>
                <div class="text-[10px] text-slate-500 mt-1">${site.type} • ${modeLabel}</div>
            `;
            container.appendChild(alertDiv);
        }
    });
}

// DETAILS PANEL
function showDetails(site) {
    const risk = currentMode === 'hydro' ? site.hydroRisk : site.bioRisk;
    const panel = document.getElementById('detail-panel');
    const content = document.getElementById('detail-content');

    panel.classList.remove('hidden');

    const factors = currentMode === 'hydro' ? site.hydroFactors : site.bioFactors;

    let factorsHTML = '';
    for (const [key, value] of Object.entries(factors)) {
        factorsHTML += `
            <div class="mb-5">
                <div class="flex justify-between text-[10px] font-bold text-slate-400 uppercase mb-2">
                    <span>${key}</span>
                    <span class="text-slate-700">${value}%</span>
                </div>
                <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div class="bg-${currentMode === 'hydro' ? 'emerald' : 'blue'}-500 h-full transition-all duration-1000" style="width: ${value}%"></div>
                </div>
            </div>
        `;
    }

    content.innerHTML = `
        <div class="mb-6">
            <p class="text-[10px] font-black uppercase tracking-widest ${risk > 75 ? 'text-red-500' : (risk > 45 ? 'text-orange-500' : 'text-emerald-500')}">
                ${risk > 75 ? 'NIVEAU CRITIQUE' : (risk > 45 ? 'NIVEAU MODÉRÉ' : 'NIVEAU FAIBLE')}
            </p>
            <h2 class="text-2xl font-black tracking-tight mt-1">${site.name}</h2>
            <p class="text-xs text-slate-500 mt-1">${site.type} • Lat ${site.lat.toFixed(3)}, Lon ${site.lon.toFixed(3)}</p>
        </div>

        <div class="p-5 rounded-3xl bg-white/70 border border-white shadow-inner mb-6">
            <div class="flex justify-between items-end">
                <div>
                    <p class="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Score de Risque</p>
                    <p class="text-4xl font-black tracking-tight ${risk > 75 ? 'text-red-500' : (risk > 45 ? 'text-orange-500' : 'text-emerald-500')}">${risk}%</p>
                </div>
                <div class="text-right text-[10px] text-slate-500">
                    Mode: <span class="font-bold">${currentMode === 'hydro' ? 'HydroScope' : 'BioScope'}</span>
                </div>
            </div>
        </div>

        <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-4 text-center">Analyse des Facteurs</h3>
        ${factorsHTML}

        <div class="mt-8 p-6 bg-slate-50 rounded-3xl border border-slate-100 text-xs text-slate-500 leading-relaxed text-center italic">
            ${currentMode === 'hydro'
                ? `"HydroScope combine météo + signaux plastiques pour anticiper un ‘flush’ vers la mer."`
                : `"BioScope estime le stress habitat (NDVI + chaleur + extrêmes pluie) pour protéger la biodiversité."`
            }
        </div>
    `;
}

function closeDetails() {
    document.getElementById('detail-panel').classList.add('hidden');
}

// Wire buttons
document.getElementById('btn-hydro').addEventListener('click', () => switchMode('hydro'));
document.getElementById('btn-bio').addEventListener('click', () => switchMode('bio'));

// INITIAL LOAD: fetch real data then render
(async function init() {
    try {
        sites = await loadSitesFromAPI();
        if (!sites.length) throw new Error("Empty API data");
    } catch (e) {
        console.warn("Using demo data (API failed):", e);
        sites = demoSites;
    }
    renderApp();
})();
