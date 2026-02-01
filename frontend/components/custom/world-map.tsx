import { DottedMap } from "../ui/dotted-map"

const markers = [
  { lat: 40.7128, lng: -74.0060, size: 0.3 }, // New York (HQ / Pearl River nearby)
  { lat: 41.0587, lng: -74.0213, size: 0.3 }, // Pearl River, NY - Vaccine R&D + manufacturing
  { lat: 42.6583, lng: -71.1368, size: 0.3 }, // Andover, MA - R&D + manufacturing
  { lat: 42.3736, lng: -71.1097, size: 0.3 }, // Cambridge, MA - R&D
  { lat: 41.3501, lng: -72.0784, size: 0.3 }, // Groton, CT - R&D
  { lat: 32.8328, lng: -117.2713, size: 0.3 }, // La Jolla, CA - R&D (oncology)

  { lat: 42.2917, lng: -85.5872, size: 0.3 }, // Kalamazoo, MI - API + drug product manufacturing
  { lat: 38.3708, lng: -97.6642, size: 0.3 }, // McPherson, KS - sterile injectables
  { lat: 43.0972, lng: -89.5043, size: 0.3 }, // Middleton, WI - biologics manufacturing
  { lat: 39.5584, lng: -84.3044, size: 0.3 }, // Franklin, OH - heparin API
  { lat: 47.8145, lng: -122.2057, size: 0.3 }, // North Creek, WA - antibody drug conjugates
  { lat: 42.6806, lng: -83.1338, size: 0.3 }, // Rochester, MI - penicillin manufacturing
  { lat: 35.9382, lng: -77.7905, size: 0.3 }, // Rocky Mount, NC - sterile injectables
  { lat: 35.4799, lng: -79.1803, size: 0.3 }, // Sanford, NC - multi-product manufacturing

  { lat: 53.3380, lng: -6.4480, size: 0.3 }, // Grange Castle, Ireland - large biologics plant
  { lat: 53.1817, lng: -6.7950, size: 0.3 }, // Newbridge, Ireland - solid dose manufacturing
  { lat: 50.8503, lng: 4.3517, size: 0.3 },  // Brussels, Belgium - Clinical Research Unit
  { lat: 51.0746, lng: 4.2884, size: 0.3 }, // Puurs, Belgium - major manufacturing & packaging
  { lat: 50.8833, lng: 4.4725, size: 0.33 }, // Zaventem, Belgium - Pfizer site
  { lat: 50.8333, lng: 4.3167, size: 0.3 }, // Anderlecht, Belgium - Pfizer site
  { lat: 40.6019, lng: 22.9873, size: 1 }, // Thessaloniki, Greece - CDI -


  { lat: 31.2304, lng: 121.4737, size: 0.3 }, // Shanghai - Asia-Pacific R&D hub
  { lat: 30.5928, lng: 114.3055, size: 0.3 }, // Wuhan - affiliated R&D site
  { lat: 1.3345, lng: 103.6450, size: 0.3 }, // Tuas, Singapore - API manufacturing facility
  { lat: 13.0792, lng: 80.2790, size: 0.3  }, // Chennai, India - Drug development centre
  { lat: 31.1048, lng: 121.3150, size: 0.3 }, // Shanghai - secondary Pfizer development/processing facility

  { lat: 1.2990, lng: 103.6300, size: 0.3 }, // Tuas, Singapore - API manufacturing
];


export function WorldMap() {
  return (
    <div className="absolute top-4 right-2 h-[300px] w-full scale-75 border-none [mask-image:linear-gradient(to_top,transparent_10%,#000_100%)] transition-all duration-300 ease-out group-hover:scale-90">
        <div className="flex-1 max-h-[0]">
            <DottedMap markers={markers} />
        </div>
    </div>

  )
}
