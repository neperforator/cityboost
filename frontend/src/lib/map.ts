import { Map, NavigationControl, setWorkerUrl, type StyleSpecification } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'

// MapLibre по умолчанию ищет worker рядом со своим чанком. После сборки Vite
// чанк получает хеш, поэтому явно указываем URL, который Vite копирует в assets.
setWorkerUrl(workerUrl)

/** Центр карты по умолчанию (Витебск). */
export const DEFAULT_CENTER: [number, number] = [30.2049, 55.1904]
export const DEFAULT_ZOOM = 12

/** Границы Витебска в формате MapLibre: [юго-запад, северо-восток]. */
export const VITEBSK_BOUNDS: [[number, number], [number, number]] = [
  [30.07, 55.13],
  [30.33, 55.32],
]

/** Проверить, что координаты находятся в границах Витебска. */
export function isInVitebsk(lat: number, lng: number): boolean {
  const [[west, south], [east, north]] = VITEBSK_BOUNDS
  return lat >= south && lat <= north && lng >= west && lng <= east
}

/**
 * Базовый стиль с растровыми тайлами OpenStreetMap.
 * MapLibre требует явного style, поэтому описываем его один раз для всех карт.
 */
export const OSM_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      maxzoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    },
  },
  layers: [
    {
      id: 'osm',
      type: 'raster',
      source: 'osm',
    },
  ],
}

export interface CreateMapOptions {
  center?: [number, number]
  zoom?: number
  attributionControl?: boolean
  navigationControl?: boolean
}

/** Создаёт карту с единым стилем и базовыми настройками. */
export function createMap(
  container: HTMLElement,
  options: CreateMapOptions = {},
): Map {
  const map = new Map({
    container,
    style: OSM_STYLE,
    center: options.center ?? DEFAULT_CENTER,
    zoom: options.zoom ?? DEFAULT_ZOOM,
    attributionControl: (options.attributionControl ?? true) ? {} : false,
    // Для плоской карты заявок поворот и наклон не нужны.
    dragRotate: false,
    pitchWithRotate: false,
  })

  if (options.navigationControl ?? true) {
    map.addControl(
      new NavigationControl({ showCompass: false }),
      'top-left',
    )
  }

  return map
}
