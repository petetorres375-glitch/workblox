const MAX_DIMENSION = 1600;
const JPEG_QUALITY = 0.82;

// Resizes/re-encodes a photo client-side so uploads stay fast on mobile.
// If the browser can't decode the source format (e.g. HEIC on most Android
// browsers, which — unlike Safari — have no built-in HEIC decoder), this
// throws; the caller should fall back to uploading the original file as-is
// and let the backend (which can decode HEIC via Pillow) normalize it instead.
export async function compressImage(file) {
  const img = await loadImage(file);
  const { width, height } = fitDimensions(img.naturalWidth, img.naturalHeight, MAX_DIMENSION);

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  canvas.getContext("2d").drawImage(img, 0, 0, width, height);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("Could not process that photo."))),
      "image/jpeg",
      JPEG_QUALITY
    );
  });
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("Could not decode image")); };
    img.src = url;
  });
}

function fitDimensions(width, height, max) {
  if (width <= max && height <= max) return { width, height };
  const scale = max / Math.max(width, height);
  return { width: Math.round(width * scale), height: Math.round(height * scale) };
}
