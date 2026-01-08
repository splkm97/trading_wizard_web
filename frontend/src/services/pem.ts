/**
 * PEM file export/import utilities.
 */

/**
 * Convert ArrayBuffer to PEM format string.
 */
export function arrayBufferToPem(buffer: ArrayBuffer, label: string): string {
  const base64 = arrayBufferToBase64(buffer);
  const lines = base64.match(/.{1,64}/g) || [];
  return `-----BEGIN ${label}-----\n${lines.join('\n')}\n-----END ${label}-----`;
}

/**
 * Parse PEM format string to ArrayBuffer.
 */
export function pemToArrayBuffer(pem: string, label: string): ArrayBuffer {
  const regex = new RegExp(
    `-----BEGIN ${label}-----\\s*([A-Za-z0-9+/=\\s]+)\\s*-----END ${label}-----`
  );
  const match = pem.match(regex);

  if (!match) {
    throw new Error(`Invalid PEM format for ${label}`);
  }

  const base64 = match[1].replace(/\s/g, '');
  return base64ToArrayBuffer(base64);
}

/**
 * Convert ArrayBuffer to base64 string.
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert base64 string to ArrayBuffer.
 */
export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Download PEM content as a file.
 */
export function downloadPemFile(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'application/x-pem-file' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Read PEM file content.
 */
export function readPemFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const content = reader.result as string;
      resolve(content);
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

/**
 * Validate PEM file format.
 */
export function validatePemFormat(content: string, label: string): boolean {
  const regex = new RegExp(
    `-----BEGIN ${label}-----\\s*[A-Za-z0-9+/=\\s]+\\s*-----END ${label}-----`
  );
  return regex.test(content);
}
