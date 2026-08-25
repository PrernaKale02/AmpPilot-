/**
 * Mock nearby EV charging stations, nearest first.
 *
 * Shape mirrors what the future FastAPI
 * `GET /charging-stations?latitude={lat}&longitude={lng}&radius={radius}`
 * endpoint will return, so chargingService can swap its implementation
 * without any change to NearbyStationsScreen.
 *
 * `status` on each station is one of "available", "busy", "offline", or
 * `null` when the provider does not genuinely report availability. See
 * `components/stationStatusStyles.js`.
 *
 * Coordinates are real points around Mumbai so the data stays plausible
 * once a real map is added.
 *
 * @typedef {Object} ChargingStation
 * @property {string} id - Stable station id, e.g. "cs-001".
 * @property {string} name - Display name of the station.
 * @property {string} network - Operator running the station, e.g. "Tata Power".
 * @property {string} address - Single-line human-readable address.
 * @property {number} latitude - WGS84 decimal degrees.
 * @property {number} longitude - WGS84 decimal degrees.
 * @property {number} distanceKm - Distance from the search origin, in km.
 * @property {"available"|"busy"|"offline"|null} status - Current availability.
 * @property {number} availableConnectors - Connectors currently free.
 * @property {number} totalConnectors - Connectors installed at the site.
 * @property {number} maxPowerKw - Peak power of the fastest connector, in kW.
 * @property {string[]} connectorTypes - e.g. ["CCS2", "Type2"].
 * @property {"AC"|"DC"|"BOTH"} chargerType - Kind of charging offered.
 * @property {number|null} pricePerKwh - Null when the operator doesn't publish pricing.
 * @property {string} currency - ISO 4217 code, e.g. "INR".
 * @property {boolean} isOpen24Hours - Whether the site never closes.
 * @property {string|null} hours - Opening hours when not open 24/7, else null.
 * @property {string|null} lastUpdatedAt - ISO timestamp availability was last refreshed.
 */

/** @type {ChargingStation[]} */
export const chargingStationsMock = [
  {
    id: "cs-001",
    name: "Tata Power EZ Charge — Phoenix Marketcity",
    network: "Tata Power",
    address: "Phoenix Marketcity, Kurla West, Mumbai",
    latitude: 19.0866,
    longitude: 72.8891,
    distanceKm: 1.2,
    status: "available",
    availableConnectors: 4,
    totalConnectors: 6,
    maxPowerKw: 120,
    connectorTypes: ["CCS2", "Type2"],
    chargerType: "DC",
    pricePerKwh: 18.5,
    currency: "INR",
    isOpen24Hours: true,
    hours: null,
    lastUpdatedAt: "2026-08-14T09:20:00Z",
  },
  {
    id: "cs-002",
    name: "Statiq Charging Hub — Lower Parel",
    network: "Statiq",
    address: "Kamala Mills Compound, Lower Parel, Mumbai",
    latitude: 19.0036,
    longitude: 72.8296,
    distanceKm: 2.4,
    status: "busy",
    availableConnectors: 0,
    totalConnectors: 4,
    maxPowerKw: 60,
    connectorTypes: ["CCS2"],
    chargerType: "DC",
    pricePerKwh: 21,
    currency: "INR",
    isOpen24Hours: true,
    hours: null,
    lastUpdatedAt: "2026-08-14T09:12:00Z",
  },
  {
    id: "cs-003",
    name: "Ather Grid — Bandra Linking Road",
    network: "Ather Grid",
    address: "Linking Road, Bandra West, Mumbai",
    latitude: 19.0607,
    longitude: 72.8302,
    distanceKm: 3.1,
    status: "available",
    availableConnectors: 2,
    totalConnectors: 2,
    maxPowerKw: 7.4,
    connectorTypes: ["Type2"],
    chargerType: "AC",
    pricePerKwh: 12,
    currency: "INR",
    isOpen24Hours: false,
    hours: "7:00 AM - 11:00 PM",
    lastUpdatedAt: "2026-08-14T08:55:00Z",
  },
  {
    id: "cs-004",
    name: "Jio-bp pulse — Andheri East",
    network: "Jio-bp pulse",
    address: "Chakala, Andheri East, Mumbai",
    latitude: 19.1136,
    longitude: 72.8697,
    distanceKm: 4.6,
    status: "available",
    availableConnectors: 3,
    totalConnectors: 8,
    maxPowerKw: 60,
    connectorTypes: ["CCS2", "Type2"],
    chargerType: "BOTH",
    pricePerKwh: 20.5,
    currency: "INR",
    isOpen24Hours: true,
    hours: null,
    lastUpdatedAt: "2026-08-14T09:18:00Z",
  },
  {
    id: "cs-005",
    name: "ChargeZone Supercharger — Vashi",
    network: "ChargeZone",
    address: "Sector 17, Vashi, Navi Mumbai",
    latitude: 19.0771,
    longitude: 72.9986,
    distanceKm: 5.8,
    status: "offline",
    availableConnectors: 0,
    totalConnectors: 4,
    maxPowerKw: 150,
    connectorTypes: ["CCS2", "CHAdeMO"],
    chargerType: "DC",
    pricePerKwh: 22,
    currency: "INR",
    isOpen24Hours: true,
    hours: null,
    lastUpdatedAt: "2026-08-14T06:40:00Z",
  },
  {
    id: "cs-006",
    name: "Zeon Charging — Powai Hiranandani",
    network: "Zeon Charging",
    address: "Hiranandani Gardens, Powai, Mumbai",
    latitude: 19.1197,
    longitude: 72.9051,
    distanceKm: 7.2,
    status: null,
    availableConnectors: 0,
    totalConnectors: 3,
    maxPowerKw: 50,
    connectorTypes: ["CCS2"],
    chargerType: "DC",
    pricePerKwh: null,
    currency: "INR",
    isOpen24Hours: false,
    hours: "6:00 AM - 10:00 PM",
    lastUpdatedAt: null,
  },
  {
    id: "cs-007",
    name: "Relux Electric — Worli Sea Face",
    network: "Relux Electric",
    address: "Worli Sea Face, Worli, Mumbai",
    latitude: 19.0176,
    longitude: 72.8156,
    distanceKm: 8.9,
    status: "busy",
    availableConnectors: 1,
    totalConnectors: 6,
    maxPowerKw: 22,
    connectorTypes: ["Type2"],
    chargerType: "AC",
    pricePerKwh: 14,
    currency: "INR",
    isOpen24Hours: true,
    hours: null,
    lastUpdatedAt: "2026-08-14T09:05:00Z",
  },
  {
    id: "cs-008",
    name: "Fortum Charge & Drive — Viviana Mall",
    network: "Fortum",
    address: "Viviana Mall, Eastern Express Highway, Thane",
    latitude: 19.2183,
    longitude: 72.9781,
    distanceKm: 11.4,
    status: "available",
    availableConnectors: 5,
    totalConnectors: 6,
    maxPowerKw: 50,
    connectorTypes: ["CCS2", "CHAdeMO", "Type2"],
    chargerType: "BOTH",
    pricePerKwh: 19.75,
    currency: "INR",
    isOpen24Hours: false,
    hours: "9:00 AM - 11:00 PM",
    lastUpdatedAt: "2026-08-14T08:30:00Z",
  },
];
