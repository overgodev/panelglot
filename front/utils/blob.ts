export const blobToDataUrl = (blob: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });

export const dataUrlToBlob = (dataUrl: string): Blob => {
  const [header, base64] = dataUrl.split(",", 2);
  const mime = /data:([^;]+)/.exec(header)?.[1] ?? "application/octet-stream";
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type: mime });
};

export const dataUrlToFile = (dataUrl: string, filename: string): File => {
  const blob = dataUrlToBlob(dataUrl);
  return new File([blob], filename, { type: blob.type });
};
